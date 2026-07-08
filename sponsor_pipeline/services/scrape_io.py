"""Helpers for standalone scrape scripts (no CLI dependency)."""

from __future__ import annotations

from pathlib import Path

from sponsor_pipeline.models import CrawlResult
from sponsor_pipeline.services.scraper import normalize_url


def read_urls(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def append_url(path: Path, url: str) -> bool:
    """Append a URL if it is not already listed. Returns True if appended."""
    normalized = normalize_url(url)
    existing = {normalize_url(line) for line in read_urls(path)}
    if normalized in existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(normalized + "\n")
    return True


def write_email_results(
    output_path: Path,
    results: list[CrawlResult],
    *,
    append: bool = False,
    log_path: Path | None = None,
) -> None:
    lines: list[str] = []
    for result in results:
        lines.append(f"Website: {result.start_url}")
        lines.extend(result.emails)
        lines.append("")
        if log_path:
            _log_crawl(log_path, result)

    text = "\n".join(lines)
    if append and output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"
        text = existing + text
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _log_crawl(log_path: Path, result: CrawlResult) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"Website: {result.start_url}\n")
        handle.write(f"Pages crawled: {result.pages_crawled}\n")
        for email in result.emails:
            handle.write(f"Found email: {email}\n")
        handle.write("\n")
