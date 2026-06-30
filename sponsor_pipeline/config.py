# Settings management for the sponsor research pipeline
# It reads the configuration from env.example and exposes typed, validated values to the rest of the pipeline

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

@dataclass
class Settings:
    """
    Centralized configuration for the entire pipeline from environment variables defined in .env
    Used by WebScraperService, SponsorScoringService, PipelineOrchestrator, and SponsorRepository
    """
    openai_api_key: str
    openai_model: str
    sponsor_csv_path: Path
    min_overall_score: float
    max_crawl_pages: int
    max_emails_per_site: int
    mlh_events_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from a .env file
        Raises:
            ValueError: if OPENAI_API_KEY is missing or still set as a placeholder from env.example
        """
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-key-here":
            raise ValueError(
                "OPENAI_API_KEY is not set. Copy env.example to .env and add your API key."
            )

        return cls(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            sponsor_csv_path=Path(os.getenv("SPONSOR_CSV_PATH", "data/sponsors.csv")),
            min_overall_score=float(os.getenv("MIN_OVERALL_SCORE", "6.0")),
            max_crawl_pages=int(os.getenv("MAX_CRAWL_PAGES", "50")),
            max_emails_per_site=int(os.getenv("MAX_EMAILS_PER_SITE", "5")),
            mlh_events_url=os.getenv("MLH_EVENTS_URL", "https://www.mlh.io/seasons/2026/events"),
        )