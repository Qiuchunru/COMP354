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

from sponsor_pipeline.models import (
    Company as PipelineCompany,
    CrawlResult,
    EvidenceCategory,
)
from sponsor_pipeline.services.sponsor_evaluator.schemas import (
    Company as EvaluatorCompany,
    Evidence as EvaluatorEvidence,
)


def crawl_to_evidence(crawl: CrawlResult) -> EvaluatorEvidence:
    """
    Takes what the scraper collected (CrawlResult)
    and reorganizes it into (EvaluatorEvidence)
    """
    # 1 empty list per evaluator bucket
    hiring: list[str] = []
    developer: list[str] = []
    past: list[str] = []
    contact: list[str] = []
    size: list[str] = []
    canada: list[str] = []

    # the scraper tags every piece of evidence with a category (ex:HIRING_SIGNAL)
    # we sort each one into the matching evaluator bucket
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

    # emails the scraper found on the site -> contact signals
    for email in crawl.emails:
        contact.append(f"Public email found: {email}")

    # social links (LinkedIn, Twitter...) -> contact signals
    for link in crawl.social_links:
        contact.append(f"{link.type.value}: {link.value} ({link.source_url})")

    # page text: if they mention employees/funding -> size signal
    #            if they're from a team/about page -> contact signal
    for url, text in crawl.page_snippets.items():
        lower = text.lower()
        if any(word in lower for word in ("employee", "funding", "series ", "startup")):
            size.append(f"From {url}: {text[:200]}")
        if "team" in url.lower() or "about" in url.lower():
            contact.append(f"Team/about page: {url}")

    # dedupe each bucket before returning so the LLM doesnt get confused
    return EvaluatorEvidence(
        hiring_signals=_dedupe(hiring),
        developer_products=_dedupe(developer),
        past_sponsorships=_dedupe(past),
        contact_signals=_dedupe(contact),
        company_size_signals=_dedupe(size),
        canada_signals=_dedupe(canada),
    )


def pipeline_company_to_evaluator(company: PipelineCompany) -> EvaluatorCompany:
    """
    the pipeline and the evaluator both have a Company object but they are of different types
    this just copies the fields the evaluator needs out of the pipeline's version
    """
    return EvaluatorCompany(
        name=company.name,
        website=company.website,
        industry=company.industry,
    )


def _dedupe(items: list[str]) -> list[str]:
    """
    Removes duplicate strings from a list (case-insensitive), keeping the first occurrence.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
