from __future__ import annotations

from sponsor_pipeline.logger import get_logger
from sponsor_pipeline.models import Company, Priority, SponsorScore
from sponsor_pipeline.services.scoring import SponsorScoringService

logger = get_logger(__name__)


class LeadFilter:
    def __init__(
        self, scoring_service: SponsorScoringService, min_overall: float = 6.0
    ) -> None:
        self._scoring_service = scoring_service
        self._min_overall = min_overall

    def filter_by_threshold(
        self, companies: list[Company]
    ) -> tuple[list[Company], list[Company]]:
        scores = self._scoring_service.get_scores()
        score_by_company = {s.company.id: s for s in scores}
        passed: list[Company] = []
        rejected: list[Company] = []
        for company in companies:
            score = score_by_company.get(company.id)
            if score and score.overall_score >= self._min_overall:
                passed.append(company)
            else:
                rejected.append(company)
        logger.info(
            "Lead threshold %.1f kept %s company candidate(s) and rejected %s",
            self._min_overall,
            len(passed),
            len(rejected),
        )
        return passed, rejected

    def assign_priority(self, score: SponsorScore) -> Priority:
        if score.overall_score >= 8.0:
            return Priority.HIGH
        if score.overall_score >= 6.5:
            return Priority.MEDIUM
        return Priority.LOW
