from __future__ import annotations

import json

from sponsor_pipeline.llm.client import LLMClient
from sponsor_pipeline.models import (
    Company,
    CompanySize,
    CrawlResult,
    Evidence,
    SponsorMotivation,
    SponsorScore,
)
from sponsor_pipeline.prompts.templates import PromptTemplateRegistry
from sponsor_pipeline.services.crawl_evidence import format_crawl_for_prompt


class SponsorScoringService:
    def __init__(self, llm: LLMClient, prompts: PromptTemplateRegistry) -> None:
        self._llm = llm
        self._prompts = prompts
        self._scores: dict[str, SponsorScore] = {}

    def score_company(
        self,
        company: Company,
        evidence: list[Evidence],
        crawl: CrawlResult | None = None,
    ) -> SponsorScore:
        evidence_payload = [
            {
                "category": e.category.value,
                "description": e.description,
                "source_url": e.source_url,
            }
            for e in evidence
        ]
        crawl_context = format_crawl_for_prompt(crawl) if crawl else ""
        result = self._llm.complete_structured(
            self._prompts.get_scoring_prompt()
            + f"\n\nCompany: {company.name}\nWebsite: {company.website}\n"
            + f"Industry: {company.industry}\nSources: {[s.value for s in company.discovery_sources]}\n"
            + f"Evidence:\n{json.dumps(evidence_payload, indent=2)}\n\n"
            + (f"Website research:\n{crawl_context}" if crawl_context else ""),
            """{
  "talent_score": 0.0,
  "developer_adoption_score": 0.0,
  "brand_community_score": 0.0,
  "accessibility_score": 0.0,
  "budget_likelihood_score": 0.0,
  "overall_score": 0.0,
  "primary_motivations": ["hiring_talent"],
  "company_size": "unknown",
  "scoring_rationale": "string"
}""",
        )
        score = SponsorScore(
            company_id=company.id,
            talent_score=_float(result.get("talent_score")),
            developer_adoption_score=_float(result.get("developer_adoption_score")),
            brand_community_score=_float(result.get("brand_community_score")),
            accessibility_score=_float(result.get("accessibility_score")),
            budget_likelihood_score=_float(result.get("budget_likelihood_score")),
            overall_score=_float(result.get("overall_score")),
            primary_motivations=_motivations(result.get("primary_motivations", [])),
            scoring_rationale=str(result.get("scoring_rationale", "")),
            company_size=_company_size(result.get("company_size")),
        )
        self._scores[company.id] = score
        return score

    def score_batch(
        self, companies: list[Company], evidence_map: dict[str, list[Evidence]]
    ) -> list[SponsorScore]:
        return [
            self.score_company(company, evidence_map.get(company.id, []))
            for company in companies
        ]

    def get_scores(self) -> list[SponsorScore]:
        return list(self._scores.values())

    def get_score(self, company_id: str) -> SponsorScore | None:
        return self._scores.get(company_id)

    def load_scores(self, scores: list[SponsorScore]) -> None:
        for score in scores:
            self._scores[score.company_id] = score


def _float(value: object) -> float:
    try:
        return max(0.0, min(10.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _motivations(raw: list) -> list[SponsorMotivation]:
    results: list[SponsorMotivation] = []
    for item in raw:
        try:
            results.append(SponsorMotivation(str(item)))
        except ValueError:
            continue
    return results


def _company_size(raw: object) -> CompanySize:
    try:
        return CompanySize(str(raw))
    except ValueError:
        return CompanySize.UNKNOWN
