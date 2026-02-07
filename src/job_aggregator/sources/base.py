from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import AppConfig
from ..models import JobListing


class SourceClient(ABC):
    source_name: str

    @abstractmethod
    def fetch_jobs(self, config: AppConfig) -> list[JobListing]:
        raise NotImplementedError
