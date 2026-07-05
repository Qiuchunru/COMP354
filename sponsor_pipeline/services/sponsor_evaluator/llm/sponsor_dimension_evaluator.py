"""
LLM backed evaluator for individual sponsorship dimensions
This module owns all prompt engineering and LLM interaction logic,
evaluator.py calls into this module and receives structured results back
rather than touching a prompt string directly

The abstract class SponsorDimensionEvaluator is the contract evaluator.py depends on
and ClaudeSponsorDimensionEvaluator is the concrete implementation that calls the Claude API
"""

from __future__ import annotations

import anthropic
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sponsor_pipeline.services.sponsor_evaluator.criteria import EvaluationCriterion
from sponsor_pipeline.services.sponsor_evaluator.schemas import (
    Company,
    Confidence,
    CriterionScore,
    Evidence,
    SponsorMotivation,
)


# ---------------------------------------------------------------------------
# Summary result  produced  after all  criterion scores are collected
# ---------------------------------------------------------------------------

@dataclass
class SponsorEvaluationSummary:
    """
    evaluation fields that require looking across all six criteria
    Produced by an LLM call after individual dimension scores are known
    """

    motivations: list[SponsorMotivation]
    """Why this company would sponsor, may. be more than one factor"""

    confidence: Confidence
    """How well-supported the evaluation is given the available evidence"""

    explanation: str
    """Short paragraph summarising the overall evaluation for a human reader"""

    key_strengths: list[str]
    """The strongest reasons this company is worth pursuing"""

    potential_weaknesses: list[str]
    """Risks or gaps that may make this company harder to close"""

    recommended_outreach_angle: str
    """The specific pitch angle most likely to resonate with this company"""

    recommended_contact_role: str
    """Job title or role at this company most likely to own the sponsorship decision"""


# ---------------------------------------------------------------------------
# Abstract interface, evaluator.py depends on this, not on any concrete impl
# ---------------------------------------------------------------------------

class SponsorDimensionEvaluator(ABC):
    """
    the contract between evaluator.py and the LLM layer
    Concrete implementations live in this module and handle prompt construction,
    LLM calls, response parsing. evaluator.py just calls the two methods
    evaluate_dimension and evaluate_summary.
    """

    @abstractmethod
    def evaluate_dimension(
        self,
        criterion: EvaluationCriterion,
        company: Company,
        evidence: Evidence,
    ) -> CriterionScore:
        """
        called per-dimension to score a single sponsorship dimension for the given company
        Args:
            criterion:  The dimension to evaluate (from criteria.py)
            company:    Basic company metadata
            evidence:   Structured facts collected during earlier discovery stage
        Returns:
            A CriterionScore with score (0–10) along with reasoning, and supporting evidence
        """


    @abstractmethod
    def evaluate_summary(
        self,
        company: Company,
        evidence: Evidence,
        criterion_scores: dict[str, CriterionScore],
    ) -> SponsorEvaluationSummary:
        """
        called once, it produces holistic evaluation fields after all  dimensions are scored
        Args:
            company:          Basic company metadata
            evidence:         Structured facts collected during discovery (scraping)
            criterion_scores: All six CriterionScore results keyed by criterion_key
        Returns:
            A SponsorEvaluationSummary with confidence, motivations, outreach advice...
        """


# ---------------------------------------------------------------------------
# Prompt constants for the concrete Claude implementation
# defined at module level so they can be read and tuned without digging into methods
# ---------------------------------------------------------------------------

_DIMENSION_SYSTEM_PROMPT = (
    "You are a sponsorship analyst for Hack Canada, a major Canadian university hackathon.\n"
    "Your job is to score one dimension of a company's fit as a potential sponsor.\n"
    "\n"
    "Rules:\n"
    "- Score based only on the evidence provided, never on company reputation or name recognition\n"
    "- A well-known company with no relevant evidence should score low\n"
    "- A smaller company with strong targeted evidence should score high\n"
    "- Cite the specific evidence items that drove the score in supporting_evidence"
)

_SUMMARY_SYSTEM_PROMPT = (
    "You are a sponsorship analyst for Hack Canada, a major Canadian university hackathon.\n"
    "You have already scored a company across six dimensions. Now produce a holistic summary.\n"
    "\n"
    "Rules:\n"
    "- Motivations must be grounded in the dimension scores and evidence, not assumed\n"
    "- Confidence reflects evidence volume and quality, not score height\n"
    "- The outreach angle should be concrete and specific to this company, not generic\n"
    "- Recommended contact role should be a real job title, not a vague category"
)

