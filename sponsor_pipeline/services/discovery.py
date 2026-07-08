from __future__ import annotations

import json
from urllib.parse import urlparse

from sponsor_pipeline.adapters.sources import SourceAdapter
from sponsor_pipeline.llm.client import LLMClient
from sponsor_pipeline.models import Company, DiscoverySource, RawLead
from sponsor_pipeline.prompts.templates import PromptTemplateRegistry


class CompanyDiscoveryService:
    def __init__(
        self,
        adapters: list[SourceAdapter],
        llm: LLMClient,
        prompts: PromptTemplateRegistry,
    ) -> None:
        self._adapters = adapters
        self._llm = llm
        self._prompts = prompts

    def discover_companies(
        self, sources: list[DiscoverySource] | None = None
    ) -> list[Company]:
        raw_leads: list[RawLead] = []
        for adapter in self._adapters:
            if sources and adapter.get_source_type() not in sources:
                continue
            raw_leads.extend(adapter.fetch_candidates())

        companies = self._enrich_with_ai(raw_leads)
        return _dedupe_companies(companies)

    def enrich_from_web(self, company: Company) -> Company:
        if company.website:
            return company
        result = self._llm.complete_structured(
            self._prompts.get_discovery_prompt()
            + f"\n\nFind the official website URL for: {company.name}",
            '{"website": "https://example.com"}',
        )
        website = str(result.get("website", "")).strip()
        if website.startswith("http"):
            company.website = website
        return company

    def _enrich_with_ai(self, leads: list[RawLead]) -> list[Company]:
        if not leads:
            return []

        companies: list[Company] = []
        batch_size = 25
        for i in range(0, len(leads), batch_size):
            batch = leads[i : i + batch_size]
            payload = [
                {
                    "name": lead.name,
                    "website": lead.website,
                    "source": lead.source.value,
                    "notes": lead.notes,
                }
                for lead in batch
            ]
            result = self._llm.complete(
                self._prompts.get_discovery_prompt()
                + "\n\nNormalize and filter this lead list. Drop weak or duplicate leads."
                + "\nReturn JSON only with shape: "
                '{"companies": [{"name": "string", "website": "https://...", '
                '"sources": ["mlh_event"], "industry": "string", "notes": "string"}]}'
                + "\n\nLeads:\n"
                + json.dumps(payload, indent=2),
            )
            parsed = _safe_parse(result)
            for item in parsed.get("companies", []):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                website = str(item.get("website", "")).strip()
                sources_raw = item.get("sources") or [
                    item.get("source", "manual_input")
                ]
                sources_list = []
                for s in sources_raw:
                    try:
                        sources_list.append(DiscoverySource(str(s)))
                    except ValueError:
                        sources_list.append(DiscoverySource.MANUAL_INPUT)
                companies.append(
                    Company(
                        name=name,
                        website=website if website.startswith("http") else "",
                        industry=str(item.get("industry", "")),
                        discovery_sources=sources_list
                        or [DiscoverySource.MANUAL_INPUT],
                    )
                )
        return companies


def _dedupe_companies(companies: list[Company]) -> list[Company]:
    by_key: dict[str, Company] = {}
    for company in companies:
        key = _company_key(company)
        if key in by_key:
            existing = by_key[key]
            for source in company.discovery_sources:
                if source not in existing.discovery_sources:
                    existing.discovery_sources.append(source)
            if not existing.website and company.website:
                existing.website = company.website
            if not existing.industry and company.industry:
                existing.industry = company.industry
        else:
            by_key[key] = company
    return list(by_key.values())


def _company_key(company: Company) -> str:
    if company.website:
        host = urlparse(company.website).netloc.replace("www.", "").lower()
        if host:
            return host
    return company.name.lower().strip()


def _safe_parse(text: str) -> dict:
    import re

    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"companies": []}
