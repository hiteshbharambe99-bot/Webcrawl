from __future__ import annotations

import os
from datetime import datetime

from ..config import AppConfig
from ..models import JobListing
from ..utils import build_canonical_key, parse_salary
from .base import SourceClient


ENGINE_MAP = {
    "Indeed": "indeed",
    "Jora": "jora",
    "GoogleJobs": "google_jobs",
    "LinkedIn": "google_jobs",  # LinkedIn can surface through Google Jobs provider results
}


class SerpApiSource(SourceClient):
    def __init__(self, source_name: str):
        self.source_name = source_name

    def fetch_jobs(self, config: AppConfig) -> list[JobListing]:
        source_cfg = config.sources.get(self.source_name)
        if not source_cfg or not source_cfg.enabled:
            return []
        api_key = os.getenv(source_cfg.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key env: {source_cfg.api_key_env}")

        engine = ENGINE_MAP.get(self.source_name)
        if not engine:
            return []

        jobs: list[JobListing] = []
        for keyword in config.search.keywords:
            params = {
                "engine": engine,
                "q": keyword,
                "location": (config.search.locations or ["Australia"])[0],
                "api_key": api_key,
            }
            if config.search.date_posted_days:
                params["chips"] = f"date_posted:{config.search.date_posted_days}"

            import requests

            resp = requests.get("https://serpapi.com/search", params=params, timeout=config.request_timeout_seconds)
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("jobs_results") or payload.get("organic_results") or []
            for item in items:
                raw_salary = item.get("detected_extensions", {}).get("salary") or item.get("salary", "")
                salary_min, salary_max, currency, period = parse_salary(raw_salary)
                job = JobListing(
                    source=self.source_name,
                    job_title=item.get("title", ""),
                    company=item.get("company_name", "") or item.get("company", ""),
                    location=item.get("location", ""),
                    work_type=item.get("detected_extensions", {}).get("schedule_type", ""),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    salary_period=period,
                    salary_raw_text=raw_salary or "Not listed",
                    posted_date=item.get("detected_extensions", {}).get("posted_at", "") or item.get("date", ""),
                    job_url=item.get("related_links", [{}])[0].get("link", "") if isinstance(item.get("related_links"), list) else item.get("link", ""),
                    description_snippet=(item.get("description", "") or item.get("snippet", ""))[:250],
                    job_id=str(item.get("job_id", "") or item.get("id", "")),
                    date_fetched=datetime.utcnow().isoformat(),
                )
                job.canonical_key = build_canonical_key(job)
                jobs.append(job)
        return jobs
