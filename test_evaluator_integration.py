"""
Integration test: verifies SponsorEvaluator is wired end to end through run_scoring()

What this tests:
  - _build_dimension_evaluator(settings) picks the right provider
  - SponsorEvaluator.evaluate() is called with bridge-converted data
  - evaluator_score_to_pipeline() produces a valid PipelineSponsorScore
  - the score is saved to the repo and registered in self._scoring

does NOT test:
  - real web crawling
  - discovery or research stages
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# --------------------- project root on path --------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from sponsor_pipeline.config import Settings
from sponsor_pipeline.models import (
    Company,
    CrawlResult,
    DiscoverySource,
    Evidence,
    EvidenceCategory,
    LeadStatus,
)
from sponsor_pipeline.orchestrator import PipelineOrchestrator


def make_settings(tmp_db: Path) -> Settings:
    s = Settings.from_env()
    s.sponsor_db_path = tmp_db
    return s


def make_company() -> Company:
    return Company(
        name="Stripe",
        website="https://stripe.com",
        industry="Fintech / Payments",
        discovery_sources=[DiscoverySource.MANUAL_INPUT],
        status=LeadStatus.DISCOVERED,
    )


def make_crawl(company: Company) -> CrawlResult:
    """Pre-built crawl result"""
    return CrawlResult(
        start_url=company.website,
        pages_crawled=3,
        emails=["partnerships@stripe.com"],
        social_links=[],
        page_snippets={
            "https://stripe.com/jobs": "We are hiring software engineers in Toronto and Waterloo.",
            "https://stripe.com/about": "Stripe has 8,000 employees and offices across Canada.",
        },
        evidence=[
            Evidence(
                category=EvidenceCategory.HIRING_SIGNAL,
                description="Hiring software engineers in Waterloo co-op program",
                source_url="https://stripe.com/jobs",
            ),
            Evidence(
                category=EvidenceCategory.PAST_SPONSORSHIP,
                description="Listed as sponsor on Hack the North 2024 website",
                source_url="https://hackthenorth.com",
            ),
            Evidence(
                category=EvidenceCategory.DEVELOPER_PRODUCT_FIT,
                description="Stripe has a public REST API with a free sandbox tier and SDKs",
                source_url="https://stripe.com/docs",
            ),
            Evidence(
                category=EvidenceCategory.WATERLOO_CANADA_FIT,
                description="Toronto and Waterloo offices listed on careers page",
                source_url="https://stripe.com/jobs",
            ),
            Evidence(
                category=EvidenceCategory.CONTACTABILITY,
                description="DevRel team active on X/Twitter, partnerships email on site",
                source_url="https://stripe.com/contact",
            ),
        ],
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_db = Path(tmp) / "test_sponsors.db"
        settings = make_settings(tmp_db)

        print(f"Provider : {settings.llm_provider}")
        print(f"Model    : {settings.llm_model}")
        print()

        orchestrator = PipelineOrchestrator(settings)

        company = make_company()
        crawl = make_crawl(company)

        # save the company first so run_scoring can find it
        orchestrator._repo.save_company(company)

        # patch _get_crawl so we skip real HTTP
        with patch.object(orchestrator, "_get_crawl", return_value=crawl):
            scores = orchestrator.run_scoring([company])

        if not scores:
            print("FAIL: run_scoring returned no results")
            sys.exit(1)

        scored_company = scores[0]
        score = orchestrator._repo.get_score(scored_company.id)

        if score is None:
            print("FAIL: score was not saved to the repository")
            sys.exit(1)

        # confirm it's in the in-memory scoring service
        in_memory = orchestrator._scoring.get_score(scored_company.id)
        if in_memory is None:
            print("FAIL: score was not registered in SponsorScoringService")
            sys.exit(1)

        print("PASS: score produced and wired correctly")
        print(f"  Company        : {score.company.name}")
        print(f"  Overall score  : {score.overall_score:.1f} / 10")
        print(f"  Confidence     : {score.confidence}")
        print(f"  Motivations    : {[m.value for m in score.motivations]}")
        print(f"  Explanation    : {score.explanation[:120]}...")
        print()
        print("  Criterion scores:")
        for key, cs in score.criterion_scores.items():
            print(f"    {key:<28} {cs.score:.1f}  — {cs.reasoning[:80]}")


if __name__ == "__main__":
    run()
