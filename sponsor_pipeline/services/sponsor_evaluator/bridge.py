"""
Bridge between the pipeline CrawlResult and the sponsor evaluator Evidence.
This module is the conversion layer between two different representations
of the same underlying data:

    models.Evidence      — pipeline-wide tagged observation (category + description + source)
    schemas.Evidence     — evaluator-specific structured container (6 typed lists)

The pipeline produces CrawlResult objects containing models.Evidence items.
The sponsor evaluator expects schemas.Evidence as its input format.
This file converts between the two so neither module needs to know about the other.
"""

from __future__ import annotations

from sponsor_pipeline.models import CrawlResult
from sponsor_pipeline.models import EvidenceCategory
from sponsor_pipeline.services.sponsor_evaluator.schemas import Evidence as EvaluatorEvidence


def crawl_to_evidence(crawl: CrawlResult) -> EvaluatorEvidence:
    """
    Convert a pipeline CrawlResult into evaluator Evidence.
    Maps each tagged PipelineEvidence item into the appropriate field of EvaluatorEvidence based on its EvidenceCategory.
    Also folds emails and social links into contact signals, and page snippets into size and contact signals.

    Args:
        crawl: CrawlResult produced by WebScraperService.

    Returns:
        EvaluatorEvidence ready to pass into SponsorEvaluator.evaluate().
    """
    hiring: list[str] = []
    developer: list[str] = []
    past: list[str] = []
    contact: list[str] = []
    size: list[str] = []
    canada: list[str] = []

    # Map each tagged pipeline Evidence item to the right evaluator bucket
    for item in crawl.evidence:
        line = f"{item.description} ({item.source_url})"
        if item.category == EvidenceCategory.HIRING_SIGNAL:
            hiring.append(line)
        elif item.category == EvidenceCategory.DEVELOPER_PRODUCT_FIT:
            developer.append(line)
        elif item.category == EvidenceCategory.PAST_SPONSORSHIP:
            past.append(line)
        elif item.category == EvidenceCategory.CONTACTABILITY:
            contact.append(line)
        elif item.category == EvidenceCategory.WATERLOO_CANADA_FIT:
            canada.append(line)

    # Fold emails into contact signals
    for email in crawl.emails:
        contact.append(f"Public email found: {email}")

    # Fold social links into contact signals
    for link in crawl.social_links:
        contact.append(f"{link.type.value}: {link.value} ({link.source_url})")

    # Fold page snippets — size signals from funding/employee mentions, contact signals from team/about pages
    for url, text in crawl.page_snippets.items():
        lower = text.lower()
        if any(word in lower for word in ("employee", "funding", "series ", "startup")):
            size.append(f"From {url}: {text[:200]}")
        if "team" in url.lower() or "about" in url.lower():
            contact.append(f"Team/about page: {url}")

    return EvaluatorEvidence(
        hiring_signals=_dedupe(hiring),
        developer_products=_dedupe(developer),
        past_sponsorships=_dedupe(past),
        contact_signals=_dedupe(contact),
        company_size_signals=_dedupe(size),
        canada_signals=_dedupe(canada),
    )

def _dedupe(items: list[str]) -> list[str]:
    """
    Remove duplicate strings case-insensitively, preserving order.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique