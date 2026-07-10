from __future__ import annotations

from sponsor_pipeline.logger import get_logger
from sponsor_pipeline.models import SponsorScore

logger = get_logger(__name__)


class SponsorScoringService:
    """In-memory score registry, Scores are produced by SponsorEvaluator and
    loaded here via load_scores() """

    def __init__(self) -> None:
        self._scores: dict[str, SponsorScore] = {}

    def get_scores(self) -> list[SponsorScore]:
        return list(self._scores.values())

    def get_score(self, company_id: str) -> SponsorScore | None:
        return self._scores.get(company_id)

    def load_scores(self, scores: list[SponsorScore]) -> None:
        logger.info("Loading %s saved score(s) into scoring service", len(scores))
        for score in scores:
            self._scores[score.company.id] = score
