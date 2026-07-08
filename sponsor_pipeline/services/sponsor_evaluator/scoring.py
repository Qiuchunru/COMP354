"""
Weighted score calculation for the sponsor evaluator module
this file contains the math in the pipeline
change scoring priorities --> edit the weights in criteria.py
"""

from __future__ import annotations

from sponsor_pipeline.services.sponsor_evaluator.criteria import EvaluationCriterion
from sponsor_pipeline.services.sponsor_evaluator.schemas import CriterionScore


class ScoreCalculator:
    """
    Converts a dict of CriterionScores into a single weighted overall score

    Weights come from the EvaluationCriterion objects passed at construction time
    They do not need to sum to 1.0, this class normalises them
    just the criteria that appear in both the constructor list and the provided
    criterion_scores dict contribute to the final score
    """

    def __init__(self, criteria: list[EvaluationCriterion]) -> None:
        self._criteria = criteria

    def compute(self, criterion_scores: dict[str, CriterionScore]) -> float:
        """
        Return a weighted average score in the range 0.0 – 10.0
        Steps:
            1- Filter to criteria that have a matching score
            2- Validate each score is within [0, 10]
            3- Normalise weights so they sum to 1.0
            4- Return the dot product of normalised weights and scores

        Raises:
            ValueError: if any score is outside the 0–10 range, or if no
                        criteria overlap between the constructor list and the
                        provided scores dict
        """

        # Collect criteria that have a score entry
        scored_criteria = [c for c in self._criteria if c.key in criterion_scores]

        if not scored_criteria:
            raise ValueError(
                "No criterion scores match the criteria keys "
                f"Expected one of: {[c.key for c in self._criteria]}"
            )

        # Validate score ranges
        for criterion in scored_criteria:
            score = criterion_scores[criterion.key].score
            if not (0.0 <= score <= 10.0):
                raise ValueError(
                    f"Score for '{criterion.key}' is {score!r}, "
                    "but scores must be in the range 0.0 – 10.0"
                )

        # Normalise weights
        total_weight = sum(c.weight for c in scored_criteria)
        # Guard against a degenerate configuration where all weights are zero
        if total_weight == 0.0:
            raise ValueError(
                "All criterion weights are 0.0. At least one weight must be positive"
            )

        # Weighted average
        overall = sum(
            (c.weight / total_weight) * criterion_scores[c.key].score
            for c in scored_criteria
        )

        return round(overall, 2)
