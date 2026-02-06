from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class JobListing:
    source: str
    job_title: str
    company: str
    location: str
    work_type: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "AUD"
    salary_period: str = ""
    salary_raw_text: str = "Not listed"
    posted_date: str = ""
    job_url: str = ""
    description_snippet: str = ""
    job_id: str = ""
    canonical_key: str = ""
    date_fetched: str = field(default_factory=lambda: datetime.utcnow().isoformat())


SHEET_HEADERS = [
    "source",
    "job_title",
    "company",
    "location",
    "work_type",
    "salary_min",
    "salary_max",
    "salary_currency",
    "salary_period",
    "salary_raw_text",
    "posted_date",
    "job_url",
    "description_snippet",
    "job_id",
    "canonical_key",
    "date_fetched",
]
