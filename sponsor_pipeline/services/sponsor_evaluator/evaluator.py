"""
Orchestration layer for the sponsor evaluator pipeline

This file is the connective tissue between the LLM layer and the scoring layer
it doesn't score or prompt, it just drives
the evaluation sequence from start to finish and hands back a SponsorScore

The flow is:
  1- Evaluate each of the six sponsorship dimensions via the LLM evaluator
  2- Pass all six CriterionScores to the LLM evaluator again for a holistic summary
  3- Hand the scores to ScoreCalculator to get the final weighted overall score
  4- Assemble everything into a SponsorScore and return it

change how scores are computed ----> scoring.py
change how the LLM is prompted ----> llm/sponsor_dimension_evaluator.py
"""

from __future__ import annotations

from sponsor_pipeline.services.sponsor_evaluator.criteria import (
    COMMUNITY_SPONSORSHIP,
    CRITERIA,
    DEVELOPER_ECOSYSTEM,
    OUTREACH_ACCESSIBILITY,
    SPONSORSHIP_CAPACITY,
    STRATEGIC_ALIGNMENT,
    TALENT_ACQUISITION,
)
from sponsor_pipeline.services.sponsor_evaluator.llm.sponsor_dimension_evaluator import (
    SponsorDimensionEvaluator,
)
from sponsor_pipeline.services.sponsor_evaluator.schemas import (
    Company,
    CriterionScore,
    Evidence,
    SponsorScore,
)

# scoring.py isn't yet implemented,  ScoreCalculator will live there
from sponsor_pipeline.services.sponsor_evaluator.scoring import ScoreCalculator


class SponsorEvaluator:
    """
    The main entry point for evaluating a company as a potential sponsor
    Both dependencies are injected rather than hardcoded 
    dimension_evaluator handles all LLM interaction, per-dimension scoring and
    the holistic summary call. score_calculator handles the weighted math
    if neither is provided, score_calculator defaults to the standard CRITERIA weights
    """

    def __init__(
        self,
        dimension_evaluator: SponsorDimensionEvaluator,
        score_calculator: ScoreCalculator | None = None,
    ) -> None:
        self._dimension_evaluator = dimension_evaluator
        self._score_calculator = score_calculator or ScoreCalculator(CRITERIA)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def evaluate(self, company: Company, evidence: Evidence) -> SponsorScore:
        """
        Evaluate a company and return a fully populated SponsorScore
        Scores all the dimensions, requests a holistic summary, computes the
        overall weighted score, then assembles everything into a SponsorScore,
        this is the only method callers outside this class use.
        """
        criterion_scores = self._evaluate_all_dimensions(company, evidence)
        overall_score = self._score_calculator.compute(criterion_scores)
        summary = self._dimension_evaluator.evaluate_summary(
            company, evidence, criterion_scores
        )

        return SponsorScore(
            company=company,
            criterion_scores=criterion_scores,
            overall_score=overall_score,
            motivations=summary.motivations,
            confidence=summary.confidence,
            explanation=summary.explanation,
            key_strengths=summary.key_strengths,
            potential_weaknesses=summary.potential_weaknesses,
            recommended_outreach_angle=summary.recommended_outreach_angle,
            recommended_contact_role=summary.recommended_contact_role,
        )

    # ------------------------------------------------------------------
    # Internal orchestration
    # ------------------------------------------------------------------

    def _evaluate_all_dimensions( self, company: Company, evidence: Evidence ) -> dict[str, CriterionScore]:
        """Run all dimension evaluations and collect the results into a dict keyed by criterion_key"""
        return {
            TALENT_ACQUISITION.key: self._evaluate_talent_acquisition(company, evidence),
            DEVELOPER_ECOSYSTEM.key: self._evaluate_developer_ecosystem(company, evidence),
            COMMUNITY_SPONSORSHIP.key: self._evaluate_community_sponsorship(company, evidence),
            OUTREACH_ACCESSIBILITY.key: self._evaluate_outreach_accessibility(company, evidence),
            SPONSORSHIP_CAPACITY.key: self._evaluate_sponsorship_capacity(company, evidence),
            STRATEGIC_ALIGNMENT.key: self._evaluate_strategic_alignment(company, evidence),
        }


    # ------------------------------------------------------------------
    # One method per dimension
    # each one is a thin call to the LLM evaluator scoped to its criterion
    # keeping them separate makes the flow explicit and gives us a clean
    # place to add dimension-specific logic later without touching the others
    # ------------------------------------------------------------------

    def _evaluate_talent_acquisition(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Does this company actually want to hire our students?"""
        return self._dimension_evaluator.evaluate_dimension(
            TALENT_ACQUISITION, company, evidence
        )

    def _evaluate_developer_ecosystem(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Can students realistically build something with their product during a 48-hour hackathon?"""
        return self._dimension_evaluator.evaluate_dimension(
            DEVELOPER_ECOSYSTEM, company, evidence
        )

    def _evaluate_community_sponsorship(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Have they shown up for student events and technical communities before?"""
        return self._dimension_evaluator.evaluate_dimension(
            COMMUNITY_SPONSORSHIP, company, evidence
        )

    def _evaluate_outreach_accessibility(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Is there a real person we can actually reach who has a reason to care?"""
        return self._dimension_evaluator.evaluate_dimension(
            OUTREACH_ACCESSIBILITY, company, evidence
        )

    def _evaluate_sponsorship_capacity(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Do they have the budget and the right size to be a realistic sponsor?"""
        return self._dimension_evaluator.evaluate_dimension(
            SPONSORSHIP_CAPACITY, company, evidence
        )

    def _evaluate_strategic_alignment(
        self, company: Company, evidence: Evidence
    ) -> CriterionScore:
        """ Do their goals overlap with what Hack Canada actually offers?"""
        return self._dimension_evaluator.evaluate_dimension(
            STRATEGIC_ALIGNMENT, company, evidence
        )
