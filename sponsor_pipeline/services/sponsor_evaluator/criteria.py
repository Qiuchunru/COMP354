"""Evaluation criteria for the sponsor evaluator module

This file is configuration, not logic. it defines the six dimensions used to
score a potential sponsor and the weight each dimension contributes to the
overall sponsorship score

To adjust scoring priorities, we'll edit the `weight` values
below,  weights do not need to sum to 1.0 , the scoring module normalises them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationCriterion:
    """
    A single scoring dimension used to evaluate a potential sponsor.
    Attributes:
        key: Machine-readable identifier used as a dict key and in prompts
        name: Human-readable display name
        description: What this criterion measures
        weight: Relative importance compared to other criteria
            Weights are normalised by the scoring module, so only their
            ratio to each other matters ( 2.0 vs 1.0 means twice as
            important, not worth 2 points )

        evidence_hints: Examples of evidence relevant to this criterion
            These are passed to the LLM prompt to guide its reasoning
    """

    key: str
    name: str
    description: str
    weight: float
    evidence_hints: list[str] = field(default_factory=list)



# ---------------------------------------------------------------------------
# Six evaluation criteria
# Weights are currently equal (1.0 each)  [To be adjusted!!]
# --------------------------------------------------------------------------

TALENT_ACQUISITION = EvaluationCriterion(
    key="talent_acquisition",
    name="Talent Acquisition Fit",
    description=(
        "How strongly the company benefits from recruiting Hack Canada participants, "
        "Focuses on Canadian student hiring, internships, co-ops, and new grad roles."
    ),
    weight=1.0,
    evidence_hints=[
        "Internship or co-op programs",
        "New graduate hiring",
        "University or campus recruiting",
        "Hiring in Canada (Toronto, Waterloo, Vancouver, Montreal)",
        "Waterloo, Montreal alumni at the company",
        "Campus or early talent recruiter roles",
    ],
)

DEVELOPER_ECOSYSTEM = EvaluationCriterion(
    key="developer_ecosystem",
    name="Developer Ecosystem Fit",
    description=(
        "How suitable the company's products are for hackathon participants "
        "A strong score means students can realistically build with this product "
        "during a 48-hour event."
    ),
    weight=1.0,
    evidence_hints=[
        "Public API or SDK",
        "Developer documentation",
        "Free tier or student credits",
        "Open-source projects or contributions",
        "Active developer community (Discord, Slack, forum)",
        "DevRel, developer advocate, or developer marketing roles",
    ],
)

COMMUNITY_SPONSORSHIP = EvaluationCriterion(
    key="community_sponsorship",
    name="Community Sponsorship Fit",
    description=(
        "The company's history of supporting technical communities and student events, "
        "Past sponsorship of comparable events is the strongest possible signal."
    ),
    weight=1.0,
    evidence_hints=[
        "Previous hackathon sponsorships",
        "MLH event sponsorships",
        "University club or student group sponsorships",
        "Developer conferences or community events",
        "Startup or student accelerator programs",
        "Canadian tech community initiatives",
    ],
)

OUTREACH_ACCESSIBILITY = EvaluationCriterion(
    key="outreach_accessibility",
    name="Outreach Accessibility",
    description=(
        "How realistic it is to reach the right person at this company. "
        "A high score means there is a named, reachable contact with a clear reason "
        "to care about sponsorship."
    ),
    weight=1.0,
    evidence_hints=[
        "Developer Relations or community manager",
        "Campus or university recruiter",
        "Partnerships or startup program manager",
        "Founder, CTO, CEO (for smaller companies)",
        "Public email address or contact page",
        "Active LinkedIn or X presence around students or developers",
    ],
)

SPONSORSHIP_CAPACITY = EvaluationCriterion(
    key="sponsorship_capacity",
    name="Sponsorship Capacity",
    description=(
        "Whether the company is likely to have the resources to sponsor. "
        "THE sweet-spot companies are seed-to-Series-C, 20–500 employees. "
        "Very small or very large companies typically score lower."
    ),
    weight=1.0,
    evidence_hints=[
        "Company size (headcount)",
        "Funding stage and recent rounds",
        "Revenue signals or growth trajectory",
        "Previous sponsorship activity (proxy for having a budget)",
        "Dedicated marketing, DevRel, or partnerships budget signals",
    ],
)

STRATEGIC_ALIGNMENT = EvaluationCriterion(
    key="strategic_alignment",
    name="Strategic Alignment",
    description=(
        "How well the company's goals align with Hack Canada's audience, "
        "Looks for overlap between what the company wants and what Hack Canada offers: "
        "Waterloo-heavy technical talent, student builders, and Canadian tech visibility."
    ),
    weight=1.0,
    evidence_hints=[
        "Explicit interest in Waterloo or Canadian technical talent",
        "Goal of growing developer adoption among students",
        "Desire for brand visibility in the Canadian student tech community",
        "Canadian headquarters, offices, or remote-Canada roles",
        "Alignment with hackathon themes (AI, fintech, infra, open source, etc.)",
    ],
)


# Ordered list used by the scoring module and prompt builder
CRITERIA: list[EvaluationCriterion] = [
    TALENT_ACQUISITION,
    DEVELOPER_ECOSYSTEM,
    COMMUNITY_SPONSORSHIP,
    OUTREACH_ACCESSIBILITY,
    SPONSORSHIP_CAPACITY,
    STRATEGIC_ALIGNMENT,
]

# Fast lookup by key for when a specific criterion needs to be retrieved by name by another module
CRITERIA_BY_KEY: dict[str, EvaluationCriterion] = {c.key: c for c in CRITERIA}
