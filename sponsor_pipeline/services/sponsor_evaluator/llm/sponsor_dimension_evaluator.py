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


# ---------------------------------------------------------------------------
# Evidence field metadata shared by both prompt builders
# ---------------------------------------------------------------------------

# Maps each criterion key to the Evidence field that carries its primary signals
# For this evaluation criterion, which evidence is the most important?
# it chooses what to emphasize for each criterion

_PRIMARY_EVIDENCE_FIELD: dict[str, str] = {
    "talent_acquisition":     "hiring_signals",
    "developer_ecosystem":    "developer_products",
    "community_sponsorship":  "past_sponsorships",
    "outreach_accessibility": "contact_signals",
    "sponsorship_capacity":   "company_size_signals",
    "strategic_alignment":    "canada_signals",
}

# All evidence fields with human-readable labels
# used by both the dimension and summary prompt builders
_EVIDENCE_FIELDS: list[tuple[str, str]] = [
    ("hiring_signals",       "Hiring signals"),
    ("developer_products",   "Developer products"),
    ("past_sponsorships",    "Past sponsorships"),
    ("contact_signals",      "Contact signals" ),
    ("company_size_signals", "Company size signals"),
    ("canada_signals",       "Canada signals"),
]



# ---------------------------------------------------------------------------
# ClaudeSponsorDimensionEvaluator implementation —--->  calls the Claude API
# ---------------------------------------------------------------------------
class ClaudeSponsorDimensionEvaluator(SponsorDimensionEvaluator):
    """
    Claude backed implementation of SponsorDimensionEvaluator
    builds prompts, calls the Claude API, and parses responses into
    CriterionScore and SponsorEvaluationSummary objects

    structured output strategy (tool use):
        define a tool whose input_schema matches the data we need,
        then force the model to call it with tool_choice= {"type": "tool"}
        claude must populate required fields before responding, so the
        output arrives as validated JSON 

    Approach to be adopted: client injection
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        # client is owned by the caller (API key and connection config live there)
        self._client = client
        self._model = model


    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def evaluate_dimension(
        self,
        criterion: EvaluationCriterion,
        company: Company,
        evidence: Evidence,
    ) -> CriterionScore:
        """
        Score a single sponsorship dimension for the given company
        builds a focused prompt, calls claude with a forced tool call,
        and parses the tool input into a CriterionScore
        Arguments:
            criterion: The dimension to evaluate(from criteria.py)
            company:   Basic company metadata
            evidence:  Structured facts collected during the discovery stage
        Returns:
            A CriterionScore with score (0–10), reasoning ,and supporting evidence
        Raises:
            ValueError: if the model response contains no tool_use block
        """
        prompt = self._build_dimension_prompt(criterion, company, evidence)
        tool   = self._criterion_score_tool()

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_DIMENSION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            # forcing the model to call this tool, guarantees a tool_use block
            tool_choice={"type": "tool", "name": tool["name"]},
        )

        return self._parse_criterion_score(criterion.key, response)

    def evaluate_summary(
        self,
        company: Company,
        evidence: Evidence,
        criterion_scores: dict[str, CriterionScore],
    ) -> SponsorEvaluationSummary:
        
        """
        Produces the holistic evaluation fields after all  dimensions are scored
        builds a summary prompt that includes all dimension scores and calls claude
        with a forced tool call then parses the result into a SponsorEvaluationSummary
        Argumentss:
            company:          basic company metadata
            evidence:         structured facts collected during the discovery stage
            criterion_scores: All CriterionScore results keyed by criterion_key

        Returns:
            A SponsorEvaluationSummary with motivations, confidence, outreach advice...
        Raises:
            ValueError: if the model response contains no tool_use block
        """
        prompt = self._build_summary_prompt(company, evidence, criterion_scores)
        tool   = self._summary_tool()

        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=_SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            # forcing the model to call this tool  guarantees a tool_use block
            tool_choice={"type": "tool", "name": tool["name"]},
        )

        return self._parse_summary(response)



    # ------------------------------------------------------------------
    #  Prompt builders
    # ------------------------------------------------------------------
    @staticmethod
    def _build_dimension_prompt(
        criterion: EvaluationCriterion,
        company: Company,
        evidence: Evidence,
    ) -> str:
        """ Build the user-turn message for a single dimension evaluation"""
        lines: list[str] = [f"Company: {company.name}"]
        if company.industry:
            lines.append(f"Industry: {company.industry}")
        if company.website:
            lines.append(f"Website: {company.website}")
        if company.description:
            lines.append(f"Description: {company.description}")

        lines += [
            "",
            f"Criterion to evaluate: {criterion.name}",
            f"What this measures: {criterion.description}",
            "",
            "Evidence hints (what to look for):",
        ]
        for hint in criterion.evidence_hints:
            lines.append(f"  - {hint}")


        # Primary evidence: the field that maps directly to this criterion
        primary_field = _PRIMARY_EVIDENCE_FIELD.get(criterion.key, "")
        primary_items = getattr(evidence, primary_field, []) if primary_field else []

        lines += ["", "Primary evidence (directly relevant to this criterion):"]
        if primary_items:
            for item in primary_items:
                lines.append(f"  - {item}")
        else:
            lines.append("  (none collected)")

        # supporting context: all other evidence fields so the LLM can infer across signals
        other_fields = [(f, label) for f, label in _EVIDENCE_FIELDS if f != primary_field]
        has_other = any(getattr(evidence, f, []) for f, _ in other_fields)

        lines += ["", "Additional context (all other collected evidence):"]
        if has_other:
            for field, label in other_fields:
                items = getattr(evidence, field, [])
                if items:
                    lines.append(f"  {label}:")
                    for item in items:
                        lines.append(f"    - {item}")
        else:
            lines.append("  (none)")

        lines += [
            "",
            f"Score {company.name!r} on '{criterion.name}' from 0.0 to 10.0.",
            "Base the score strictly on the evidence above, not on company reputation.",
        ]


        return "\n".join(lines)


    @staticmethod
    def _build_summary_prompt(
        company: Company,
        evidence: Evidence,
        criterion_scores: dict[str, CriterionScore],
    ) -> str:
        """ Build the user-turn message for the holistic summary call"""
        lines: list[str] = [f"Company: {company.name}"]
        if company.industry:
            lines.append(f"Industry: {company.industry}")
        if company.website:
            lines.append(f"Website: {company.website}")
        if company.description:
            lines.append(f"Description: {company.description}")

        lines += ["", "All collected evidence:"]
        has_evidence = False
        for field, label in _EVIDENCE_FIELDS:
            items = getattr(evidence, field, [])
            if items:
                has_evidence = True
                lines.append(f"  {label}:")
                for item in items:
                    lines.append(f"    - {item}")
        if not has_evidence:
            lines.append("  (none collected)")

        lines += ["", "Dimension scores already computed:"]
        for key, cs in criterion_scores.items():
            lines.append(f"  {key}: {cs.score}/10  — {cs.reasoning}")

        lines += [
            "",
            "Produce a holistic evaluation summary using all the information above.",
            "Confidence should reflect evidence volume and quality, not how high the scores are.",
        ]

        return "\n".join(lines)



    # ------------------------------------------------------------------
    # Tool schemas
    # ------------------------------------------------------------------

    @staticmethod
    def _criterion_score_tool() -> dict:
        """Tool schema that forces claude to return a structured CriterionScore"""
        return {
            "name": "record_criterion_score",
            "description": (
                "Record the evaluation score for a single sponsorship criterion. "
                "Call this tool once with your final assessment."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "number",
                        "description": "Score from 0.0 to 10.0 based on the available evidence",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "One to three sentences explaining why this score was assigned",
                    },
                    "supporting_evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The specific evidence items from the prompt that justify the score",
                    },
                },
                "required": ["score", "reasoning", "supporting_evidence"],
            },
        }

    @staticmethod
    def _summary_tool() -> dict:
        """ tool schema, forces Claude to return a structured SponsorEvaluationSummary"""
        return {
            "name": "record_evaluation_summary",
            "description": (
                "Record the holistic evaluation summary after all six criteria have been scored. "
                "Call this tool once with the complete summary."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "motivations": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["talent", "developer_adoption", "brand_awareness"],
                        },
                        "description": "Primary reasons this company would sponsor Hack Canada",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How well-supported this evaluation is given the available evidence",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Short paragraph summarising the overall evaluation for a human reader",
                    },
                    "key_strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The strongest reasons this company is worth pursuing",
                    },
                    "potential_weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Risks or gaps that may make this company harder to close",
                    },
                    "recommended_outreach_angle": {
                        "type": "string",
                        "description": "The specific pitch angle most likely to resonate with this company",
                    },
                    "recommended_contact_role": {
                        "type": "string",
                        "description": "Job title or role at this company most likely to own the sponsorship decision",
                    },
                },
                "required": [
                    "motivations",
                    "confidence",
                    "explanation",
                    "key_strengths",
                    "potential_weaknesses",
                    "recommended_outreach_angle",
                    "recommended_contact_role",
                ],
            },
        }



    # ------------------------------------------------------------------
    # response parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_criterion_score(criterion_key: str, response) -> CriterionScore:
        """
        extracts the tool_use block from a dimension response to build a CriterionScore
        tool_choice="tool" guarantees exactly one tool_use block, so finding none -->
        something unexpected happened at the API level
        """
        tool_block = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_block is None:
            raise ValueError(
                f"Claude did not return a tool_use block for criterion '{criterion_key}'. "
                f"Response stop reason: {response.stop_reason!r}"
            )

        data = tool_block.input
        return CriterionScore(
            criterion_key=criterion_key,
            score=float(data["score"]),
            reasoning=data["reasoning"],
            supporting_evidence=data.get("supporting_evidence", []),

        )


    @staticmethod
    def _parse_summary(response) -> SponsorEvaluationSummary:
        """
        extract the tool_use block from a summary response and build a SponsorEvaluationSummary
        enum values arrive as plain strings matching the enum definitions in schemas.py
        """
        tool_block = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_block is None:
            raise ValueError(
                "Claude did not return a tool_use block for the evaluation summary. "
                f"Response stop reason: {response.stop_reason!r}"
            )

        data = tool_block.input
        return SponsorEvaluationSummary(
            motivations=[SponsorMotivation(m) for m in data["motivations"]],
            confidence=Confidence(data["confidence"]),
            explanation=data["explanation"],
            key_strengths=data["key_strengths"],
            potential_weaknesses=data["potential_weaknesses"],
            recommended_outreach_angle=data["recommended_outreach_angle"],
            recommended_contact_role=data["recommended_contact_role"],
        )
