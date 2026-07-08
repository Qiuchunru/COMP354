"""
Convert CrawlResult into structured evidence for scoring and research prompts.
"""

from __future__ import annotations

from sponsor_pipeline.models import CrawlResult


def format_crawl_for_prompt(crawl: CrawlResult, max_pages: int = 12) -> str:
    """
    Convert a CrawlResult into a structured text block for LLM prompts.
    Used by SponsorScoringService and CompanyResearchService to pass website crawl data into the AI scoring and research prompts.

    Returns:
        A formatted multi-section string ready to append to an LLM prompt.
    """
    sections: list[str] = []

    if crawl.evidence:
        sections.append(
            "Evidence tags:\n"
            + "\n".join(
                f"- {e.category.value}: {e.description} [{e.source_url}]"
                for e in crawl.evidence
            )
        )

    snippets = list(crawl.page_snippets.items())[:max_pages]

    if snippets:
        sections.append(
            "Page snippets:\n"
            + "\n\n".join(f"URL: {url}\n{text}" for url, text in snippets)
        )

    if crawl.emails:
        sections.append(
            "Emails found:\n" + "\n".join(f"- {email}" for email in crawl.emails)
        )

    if crawl.social_links:
        sections.append(
            "Social links:\n"
            + "\n".join(
                f"- {link.type.value}: {link.value}" for link in crawl.social_links
            )
        )

    return "\n\n".join(sections)


def _dedupe(items: list[str]) -> list[str]:
    """
    Remove duplicate strings, case-insensitively, preserving order.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
