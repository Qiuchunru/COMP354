from __future__ import annotations

import csv
import io
from pathlib import Path

from sponsor_pipeline.logger import get_logger
from sponsor_pipeline.models import OutreachProspect, SponsorReport
from sponsor_pipeline.persistence.repository import SponsorRepository

logger = get_logger(__name__)


class ReportExporter:
    def to_markdown(
        self, report: SponsorReport, company_name: str, website: str, scores_text: str
    ) -> str:
        return f"""# Sponsor Report: {company_name}

**Website:** {website}
**Priority:** {report.priority.value}
**Suggested tier:** {report.suggested_tier.value}

## Scores
{scores_text}

## Company overview
{report.description}

## Products & services
{report.products_and_services}

## Recent launches
{chr(10).join(f"- {x}" for x in report.recent_launches) or "- None identified"}

## Past sponsorship evidence
{report.past_sponsorship_evidence}

## Canada / hiring signals
- Hires interns/new grads: {report.hires_interns_new_grads}
- Hires in Canada: {report.hires_in_canada}
- Waterloo alumni present: {report.waterloo_alumni_present}
- DevRel/recruiting staff: {report.has_devrel_or_recruiting_staff}

## Best sponsor angle
{report.best_sponsor_angle}
"""

    def to_csv(self, prospects: list[OutreachProspect]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "company",
                "website",
                "overall_score",
                "priority",
                "contact_name",
                "contact_title",
                "contact_methods",
                "best_angle",
                "suggested_tier",
            ]
        )
        for p in prospects:
            methods = "; ".join(f"{m.type.value}:{m.value}" for m in p.contact_methods)
            writer.writerow(
                [
                    p.company.name,
                    p.company.website,
                    p.score.overall_score,
                    p.report.priority.value,
                    p.primary_contact.full_name,
                    p.primary_contact.title,
                    methods,
                    p.report.best_sponsor_angle,
                    p.report.suggested_tier.value,
                ]
            )
        return buffer.getvalue()

    def export_all(self, repo: SponsorRepository, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        prospects = repo.get_outreach_ready()
        logger.info("Exporting %s outreach-ready prospect(s)", len(prospects))
        (output_dir / "prospects.csv").write_text(
            self.to_csv(prospects), encoding="utf-8"
        )
        for prospect in prospects:
            scores_text = (
                f"- Talent: {prospect.score.talent_score}/10\n"
                f"- Developer adoption: {prospect.score.developer_adoption_score}/10\n"
                f"- Brand/community: {prospect.score.brand_community_score}/10\n"
                f"- Accessibility: {prospect.score.accessibility_score}/10\n"
                f"- Budget likelihood: {prospect.score.budget_likelihood_score}/10\n"
                f"- **Overall: {prospect.score.overall_score}/10**"
            )
            slug = prospect.company.name.lower().replace(" ", "_")
            md = self.to_markdown(
                prospect.report,
                prospect.company.name,
                prospect.company.website,
                scores_text,
            )
            contact_section = (
                f"\n## Primary contact\n"
                f"**{prospect.primary_contact.full_name}** — {prospect.primary_contact.title}\n\n"
                + "\n".join(
                    f"- {m.type.value}: {m.value} (confidence {m.confidence:.0%})"
                    for m in prospect.contact_methods
                )
            )
            (output_dir / f"{slug}.md").write_text(
                md + contact_section, encoding="utf-8"
            )
        logger.info("Exported prospects CSV and %s markdown report(s)", len(prospects))
