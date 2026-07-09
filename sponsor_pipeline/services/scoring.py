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
  "overall_score": 0.0,
  "confidence": "medium",
  "explanation": "string",
  "key_strengths": ["string"],
  "potential_weaknesses": ["string"],
  "recommended_outreach_angle": "string",
  "recommended_contact_role": "string",
  "motivations": ["hiring_talent"],
  "criterion_scores": {
    "talent_acquisition": {"score": 0.0, "reasoning": "string", "supporting_evidence": []},
    "developer_ecosystem": {"score": 0.0, "reasoning": "string", "supporting_evidence": []},
    "community_sponsorship": {"score": 0.0, "reasoning": "string", "supporting_evidence": []},
    "outreach_accessibility": {"score": 0.0, "reasoning": "string", "supporting_evidence": []},
    "sponsorship_capacity": {"score": 0.0, "reasoning": "string", "supporting_evidence": []},
    "strategic_alignment": {"score": 0.0, "reasoning": "string", "supporting_evidence": []}
  }
}""",
        )

        criterion_scores = {
            k: CriterionScore(
                criterion_key=k,
                score=_float(v.get("score")),
                reasoning=str(v.get("reasoning", "")),
                supporting_evidence=list(v.get("supporting_evidence", [])),
            )
            for k, v in result.get("criterion_scores", {}).items()
        }

        score = SponsorScore(
            company=company,
            criterion_scores=criterion_scores,
            overall_score=_float(result.get("overall_score")),
            motivations=_motivations(result.get("motivations", [])),
            confidence=str(result.get("confidence", "medium")),
            explanation=str(result.get("explanation", "")),
            key_strengths=list(result.get("key_strengths", [])),
            potential_weaknesses=list(result.get("potential_weaknesses", [])),
            recommended_outreach_angle=str(result.get("recommended_outreach_angle", "")),
            recommended_contact_role=str(result.get("recommended_contact_role", "")),
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
            self._scores[score.company.id] = score


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
