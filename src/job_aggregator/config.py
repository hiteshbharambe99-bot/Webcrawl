from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchConfig:
    keywords: list[str]
    locations: list[str]
    job_type: str = ""
    date_posted_days: int | None = None
    remote: str = ""


@dataclass
class SourceConfig:
    enabled: bool = True
    provider: str = ""
    api_key_env: str = ""


@dataclass
class GoogleSheetsConfig:
    spreadsheet_id: str
    worksheet_name: str = "Jobs_AU"
    credentials_path: str = ""
    use_oauth: bool = False


@dataclass
class AppConfig:
    search: SearchConfig
    sources: dict[str, SourceConfig] = field(default_factory=dict)
    sheets: GoogleSheetsConfig | None = None
    request_timeout_seconds: int = 30
    retries: int = 3
    backoff_base_seconds: float = 1.0
    fuzzy_similarity_threshold: float = 0.9



def load_config(path: str | Path) -> AppConfig:
    import yaml

    payload: dict[str, Any] = yaml.safe_load(Path(path).read_text())
    search = SearchConfig(**payload["search"])
    sources = {
        name: SourceConfig(**cfg) for name, cfg in payload.get("sources", {}).items()
    }
    sheets = GoogleSheetsConfig(**payload["sheets"]) if "sheets" in payload else None
    return AppConfig(
        search=search,
        sources=sources,
        sheets=sheets,
        request_timeout_seconds=payload.get("request_timeout_seconds", 30),
        retries=payload.get("retries", 3),
        backoff_base_seconds=payload.get("backoff_base_seconds", 1.0),
        fuzzy_similarity_threshold=payload.get("fuzzy_similarity_threshold", 0.9),
    )
