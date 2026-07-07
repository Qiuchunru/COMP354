from __future__ import annotations

from sponsor_pipeline.llm.client import LLMClient
from sponsor_pipeline.models import (
    Company,
    ContactMethod,
    ContactMethodType,
    ContactPerson,
    ContactRole,
    CrawlResult,
    SponsorReport,
)
from sponsor_pipeline.prompts.templates import PromptTemplateRegistry
from sponsor_pipeline.services.scraper import WebScraperService

GENERIC_EMAIL_PREFIXES = (
    "info@",
    "hello@",
    "contact@",
    "support@",
    "sales@",
    "admin@",
    "help@",
    "team@",
)


class ContactDiscoveryService:
    def __init__(
        self,
        llm: LLMClient,
        scraper: WebScraperService,
        prompts: PromptTemplateRegistry,
    ) -> None:
        self._llm = llm
        self._scraper = scraper
        self._prompts = prompts

    def find_key_contacts(
        self, company: Company, report: SponsorReport, crawl: CrawlResult | None = None
    ) -> list[ContactPerson]:
        crawl = crawl or self._scraper.crawl_site(company.website)
        snippet_text = "\n\n".join(
            f"URL: {url}\n{text}"
            for url, text in list(crawl.page_snippets.items())[:12]
        )
        result = self._llm.complete_structured(
            self._prompts.get_contact_identification_prompt()
            + f"\n\nCompany: {company.name}\nWebsite: {company.website}\n"
            + f"Best angle: {report.best_sponsor_angle}\n"
            + f"Web snippets:\n{snippet_text}",
            """{"contacts": [{
  "full_name": "string",
  "title": "string",
  "role_category": "devrel",
  "relevance_score": 8.0,
  "selection_rationale": "string"
}]}""",
        )
        contacts: list[ContactPerson] = []
        for item in result.get("contacts", []):
            name = str(item.get("full_name", "")).strip()
            if not name:
                continue
            contacts.append(
                ContactPerson(
                    company_id=company.id,
                    full_name=name,
                    title=str(item.get("title", "")),
                    role_category=_role(item.get("role_category")),
                    relevance_score=_score(item.get("relevance_score")),
                    selection_rationale=str(item.get("selection_rationale", "")),
                )
            )
        contacts.sort(key=lambda c: c.relevance_score, reverse=True)
        return contacts

    def find_public_contact_info(
        self,
        contact: ContactPerson,
        company: Company,
        crawl: CrawlResult | None = None,
    ) -> list[ContactMethod]:
        crawl = crawl or self._scraper.crawl_site(company.website)
        methods = list(crawl.social_links)
        for email in crawl.emails:
            methods.append(
                ContactMethod(
                    type=ContactMethodType.EMAIL,
                    value=email,
                    source_url=crawl.start_url,
                    confidence=_email_confidence(email, contact.full_name),
                )
            )
        snippet_text = "\n\n".join(
            f"URL: {url}\n{text}"
            for url, text in list(crawl.page_snippets.items())[:10]
        )
        ai_result = self._llm.complete_structured(
            self._prompts.get_contact_enrichment_prompt()
            + f"\n\nTarget contact: {contact.full_name} ({contact.title})\n"
            + f"Company: {company.name}\nSnippets:\n{snippet_text}",
            """{"contact_methods": [{
  "type": "email",
  "value": "name@company.com",
  "source_url": "https://...",
  "confidence": 0.8
}]}""",
        )
        for item in ai_result.get("contact_methods", []):
            try:
                ctype = ContactMethodType(str(item.get("type")))
            except ValueError:
                continue
            value = str(item.get("value", "")).strip()
            if not value:
                continue
            confidence = _score(item.get("confidence"))
            if confidence > 1:
                confidence /= 10.0
            if ctype == ContactMethodType.EMAIL:
                confidence = max(
                    confidence, _email_confidence(value, contact.full_name)
                )
            methods.append(
                ContactMethod(
                    type=ctype,
                    value=value,
                    source_url=str(item.get("source_url", company.website)),
                    confidence=confidence,
                )
            )
        return _dedupe_methods(methods)


def _role(raw: object) -> ContactRole:
    try:
        return ContactRole(str(raw).lower())
    except ValueError:
        return ContactRole.OTHER


def _score(raw: object) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _email_confidence(email: str, contact_name: str) -> float:
    lower = email.lower()
    if any(lower.startswith(prefix) for prefix in GENERIC_EMAIL_PREFIXES):
        return 0.35
    if contact_name:
        parts = [part.lower() for part in contact_name.split() if len(part) > 1]
        if parts and any(part in lower for part in parts):
            return 0.85
    return 0.65


def _dedupe_methods(methods: list[ContactMethod]) -> list[ContactMethod]:
    seen: set[str] = set()
    unique: list[ContactMethod] = []
    for method in sorted(methods, key=lambda m: m.confidence, reverse=True):
        key = f"{method.type}:{method.value.lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(method)
    return unique
