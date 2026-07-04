from __future__ import annotations

from pathlib import Path

from sponsor_pipeline.adapters.sources import (
    HackathonSiteAdapter,
    JobBoardAdapter,
    MLHSourceAdapter,
    ProductLaunchAdapter,
)
from sponsor_pipeline.config import Settings
from sponsor_pipeline.export.reporter import ReportExporter
from sponsor_pipeline.llm.client import LLMClient
from sponsor_pipeline.models import (
    Company,
    CrawlResult,
    DiscoverySource,
    LeadStatus,
    OutreachProspect,
    PipelineResult,
)
from sponsor_pipeline.persistence.repository import SponsorRepository
from sponsor_pipeline.prompts.templates import PromptTemplateRegistry
from sponsor_pipeline.services.contacts import ContactDiscoveryService
from sponsor_pipeline.services.discovery import CompanyDiscoveryService
from sponsor_pipeline.services.filter import LeadFilter
from sponsor_pipeline.services.research import CompanyResearchService
from sponsor_pipeline.services.scoring import SponsorScoringService
from sponsor_pipeline.services.scraper import WebScraperService, normalize_url


class PipelineOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm = LLMClient(settings)
        self._prompts = PromptTemplateRegistry()
        # CHANGED: was settings.db_path => renamed to settings.sponsor_csv_path
        self._repo = SponsorRepository(settings.sponsor_csv_path)
        self._scraper = WebScraperService(settings)
        self._crawl_cache: dict[str, CrawlResult] = {}
        self._discovery = CompanyDiscoveryService(self._build_adapters(settings), self._llm, self._prompts)
        self._scoring = SponsorScoringService(self._llm, self._prompts)
        self._filter = LeadFilter(self._scoring, settings.min_overall_score)
        self._research = CompanyResearchService(self._llm, self._prompts, self._filter)
        self._contacts = ContactDiscoveryService(self._llm, self._scraper, self._prompts)
        self._exporter = ReportExporter()

    def run_full_pipeline(self, sources: list[DiscoverySource] | None = None) -> PipelineResult:
        companies = self.run_discovery(sources)
        scored = self.run_scoring(companies)
        passed, rejected = self._filter.filter_by_threshold(scored)
        for company in rejected:
            company.status = LeadStatus.FILTERED_OUT
            self._repo.save_company(company)
        researched = self.run_research(passed)
        prospects = self.run_contact_discovery(researched)
        return PipelineResult(
            discovered=len(companies),
            scored=len(scored),
            filtered_out=len(rejected),
            researched=len(researched),
            outreach_ready=len(prospects),
            prospects=prospects,
        )

    def run_discovery(self, sources: list[DiscoverySource] | None = None) -> list[Company]:
        companies = self._discovery.discover_companies(sources)
        enriched: list[Company] = []
        for company in companies:
            company = self._discovery.enrich_from_web(company)
            company.status = LeadStatus.DISCOVERED
            self._repo.save_company(company)
            enriched.append(company)
        return enriched

    def run_scoring(self, companies: list[Company] | None = None) -> list[Company]:
        targets = companies or self._repo.get_companies(LeadStatus.DISCOVERED)
        scored: list[Company] = []
        for company in targets:
            if not company.website:
                company = self._discovery.enrich_from_web(company)
            if not company.website:
                continue
            crawl = self._get_crawl(company.website)
            self._repo.save_evidence(company.id, crawl.evidence)
            score = self._scoring.score_company(company, crawl.evidence, crawl)
            company.status = LeadStatus.SCORED
            company.company_size = score.company_size
            self._repo.save_company(company)
            self._repo.save_score(score)
            scored.append(company)
        return scored

    def run_research(self, companies: list[Company] | None = None) -> list[Company]:
        if companies is None:
            self._scoring.load_scores(self._repo.get_scores())
            all_scored = self._repo.get_companies(LeadStatus.SCORED)
            companies, _ = self._filter.filter_by_threshold(all_scored)

        researched: list[Company] = []
        for company in companies:
            score = self._scoring.get_score(company.id) or self._repo.get_score(company.id)
            if not score:
                continue
            crawl = self._get_crawl(company.website) if company.website else None
            report = self._research.generate_report(company, score, crawl)
            company.status = LeadStatus.RESEARCHED
            self._repo.save_company(company)
            self._repo.save_report(report)
            researched.append(company)
        return researched

    def run_contact_discovery(self, companies: list[Company] | None = None) -> list[OutreachProspect]:
        targets = companies or self._repo.get_companies(LeadStatus.RESEARCHED)
        prospects: list[OutreachProspect] = []
        for company in targets:
            report = self._repo.get_report(company.id)
            score = self._scoring.get_score(company.id) or self._repo.get_score(company.id)
            if not report or not score or not company.website:
                continue
            crawl = self._get_crawl(company.website)
            contacts = self._contacts.find_key_contacts(company, report, crawl)
            if not contacts:
                continue
            primary = contacts[0]
            methods = self._contacts.find_public_contact_info(primary, company, crawl)
            primary.contact_methods = methods
            self._repo.save_contact(primary)
            company.status = LeadStatus.OUTREACH_READY
            self._repo.save_company(company)
            prospects.append(
                OutreachProspect(
                    company=company,
                    report=report,
                    score=score,
                    primary_contact=primary,
                    contact_methods=methods,
                )
            )
        return prospects

    def export_reports(self, output_dir: str | Path) -> None:
        # CHANGED: was settings.db_path.parent / "exports" => now uses sponsor_csv_path.parent / "exports" consistently
        self._exporter.export_all(self._repo, Path(output_dir))

    def _get_crawl(self, website: str) -> CrawlResult:
        key = normalize_url(website)
        if key not in self._crawl_cache:
            self._crawl_cache[key] = self._scraper.crawl_site(website)
        return self._crawl_cache[key]

    @staticmethod
    def _build_adapters(settings: Settings) -> list:
        hackathon_urls: list[str] = []
        if settings.hackathon_urls_file.exists():
            hackathon_urls = [
                line.strip()
                for line in settings.hackathon_urls_file.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip() and not line.startswith("#")
            ]
        return [
            MLHSourceAdapter(settings.mlh_events_url),
            HackathonSiteAdapter(hackathon_urls),
            JobBoardAdapter(),
            ProductLaunchAdapter(),
        ]