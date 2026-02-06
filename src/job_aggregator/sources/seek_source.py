from __future__ import annotations

from ..config import AppConfig
from ..models import JobListing
from .base import SourceClient


class SeekSource(SourceClient):
    source_name = "Seek"

    def fetch_jobs(self, config: AppConfig) -> list[JobListing]:
        source_cfg = config.sources.get(self.source_name)
        if not source_cfg or not source_cfg.enabled:
            return []
        # Intentionally skipped unless a compliant partner API/feed is configured.
        # Add integration here when approved data access is available.
        return []
