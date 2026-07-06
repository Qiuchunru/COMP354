"""
Sponsor evaluator, scores potential sponsors across six dimensions
public surface:
    SponsorEvaluator                    the main entry point (evaluator.py)
    ClaudeSponsorDimensionEvaluator     the Claude backed LLM evaluator (llm/sponsor_dimension_evaluator.py)
    SponsorScore                        the evaluation result (schemas.py)
    Company / Evidence                  input data structures (schemas.py)
"""

from sponsor_pipeline.services.sponsor_evaluator.evaluator import SponsorEvaluator
from sponsor_pipeline.services.sponsor_evaluator.llm.sponsor_dimension_evaluator import (
    ClaudeSponsorDimensionEvaluator,
)
from sponsor_pipeline.services.sponsor_evaluator.schemas import (
    Company,
    Evidence,
    SponsorScore,
)

__all__ = [
    "SponsorEvaluator",
    "ClaudeSponsorDimensionEvaluator",
    "Company",
    "Evidence",
    "SponsorScore",
]
