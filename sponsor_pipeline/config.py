"""
Settings management for the sponsor research pipeline.
Reads configuration from a .env file and exposes typed, validated values to the rest of the pipeline
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    """
    Centralized, typed configuration for the entire pipeline from environment variables defined in .env
    Used by WebScraperService, SponsorScoringService, PipelineOrchestrator, and SponsorRepository.
    """

    openai_api_key: str
    openai_model: str
    # CHANGED: was db_path (Path) pointing to sponsors.db => renamed to sponsor_csv_path to match CSV storage decision
    sponsor_csv_path: Path
    hackathon_urls_file: Path
    scrape_log_path: Path
    min_overall_score: float
    max_crawl_pages: int
    max_emails_per_site: int
    mlh_events_url: str

    @classmethod
    def from_env(cls, *, require_openai: bool = True) -> "Settings":
        """
        Load settings from a .env file in the project root.

        Raises:
            ValueError: if OPENAI_API_KEY is missing when require_openai=True.
        """
        load_dotenv()
        project_root = Path(__file__).resolve().parent.parent

        api_key = os.getenv("OPENAI_API_KEY", "")
        if require_openai and (not api_key or api_key == "your-key-here"):
            raise ValueError(
                "OPENAI_API_KEY is not set. Copy env.example to .env and add your API key."
            )

        return cls(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            # CHANGED: was SPONSOR_DB_PATH -> data/sponsors.db => now reads SPONSOR_CSV_PATH -> data/sponsors.csv
            sponsor_csv_path=Path(os.getenv("SPONSOR_CSV_PATH", str(project_root / "data" / "sponsors.csv"))),
            hackathon_urls_file=Path(os.getenv("HACKATHON_URLS_FILE", str(project_root / "data" / "hackathon_urls.txt"))),
            scrape_log_path=Path(os.getenv("SCRAPE_LOG_PATH", str(project_root / "log.txt"))),
            min_overall_score=float(os.getenv("MIN_OVERALL_SCORE", "6.0")),
            max_crawl_pages=int(os.getenv("MAX_CRAWL_PAGES", "50")),
            max_emails_per_site=int(os.getenv("MAX_EMAILS_PER_SITE", "5")),
            mlh_events_url=os.getenv("MLH_EVENTS_URL", "https://www.mlh.io/seasons/2026/events"),
        )