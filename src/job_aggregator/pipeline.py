from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime

from .config import AppConfig
from .models import JobListing
from .excel import LocalExcelWriter
from .sheets import GoogleSheetsWriter
from .sources.seek_source import SeekSource
from .sources.serpapi_source import SerpApiSource
from .utils import build_canonical_key, is_australia_job, similarity_score

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    total_fetched: int = 0
    total_kept_au: int = 0
    total_with_salary: int = 0
    total_deduped: int = 0
    total_written: int = 0
    total_updated: int = 0
    source_success: dict[str, int] | None = None
    source_fail: dict[str, str] | None = None


def retry_fetch(source, config: AppConfig) -> list[JobListing]:
    retries = config.retries
    for attempt in range(1, retries + 1):
        try:
            return source.fetch_jobs(config)
        except Exception as exc:
            if attempt >= retries:
                raise
            sleep_s = config.backoff_base_seconds * (2 ** (attempt - 1))
            logger.warning("Retry %s for %s after error: %s", attempt, source.source_name, exc)
            time.sleep(sleep_s)
    return []


def choose_better(existing: JobListing, candidate: JobListing) -> JobListing:
    existing_score = int(existing.salary_min is not None) + len(existing.description_snippet)
    candidate_score = int(candidate.salary_min is not None) + len(candidate.description_snippet)
    existing_date = existing.posted_date or ""
    candidate_date = candidate.posted_date or ""
    if candidate_score > existing_score:
        return candidate
    if candidate_score == existing_score and candidate_date > existing_date:
        return candidate
    return existing


def dedupe_jobs(jobs: list[JobListing], threshold: float) -> list[JobListing]:
    canonical_map: dict[str, JobListing] = {}
    for job in jobs:
        job.canonical_key = build_canonical_key(job)
        if job.canonical_key in canonical_map:
            canonical_map[job.canonical_key] = choose_better(canonical_map[job.canonical_key], job)
            continue

        duplicate_key = None
        for existing_key, existing_job in canonical_map.items():
            if similarity_score(job, existing_job) >= threshold:
                duplicate_key = existing_key
                break
        if duplicate_key:
            canonical_map[duplicate_key] = choose_better(canonical_map[duplicate_key], job)
        else:
            canonical_map[job.canonical_key] = job
    return list(canonical_map.values())


def run_pipeline(config: AppConfig) -> RunSummary:
    summary = RunSummary(source_success={}, source_fail={})
    all_jobs: list[JobListing] = []

    sources = [
        SeekSource(),
        SerpApiSource("Indeed"),
        SerpApiSource("Jora"),
        SerpApiSource("GoogleJobs"),
        SerpApiSource("LinkedIn"),
    ]

    for source in sources:
        try:
            jobs = retry_fetch(source, config)
            if source.source_name == "Seek" and not jobs:
                summary.source_fail[source.source_name] = "Skipped: no compliant API/feed configured"
                continue
            summary.source_success[source.source_name] = len(jobs)
            all_jobs.extend(jobs)
        except Exception as exc:
            summary.source_fail[source.source_name] = str(exc)

    summary.total_fetched = len(all_jobs)
    au_jobs = [j for j in all_jobs if is_australia_job(j)]
    summary.total_kept_au = len(au_jobs)
    summary.total_with_salary = len([j for j in au_jobs if j.salary_min is not None or j.salary_max is not None])

    deduped = dedupe_jobs(au_jobs, config.fuzzy_similarity_threshold)
    summary.total_deduped = len(au_jobs) - len(deduped)

    for job in deduped:
        if not job.salary_raw_text:
            job.salary_raw_text = "Not listed"
        job.date_fetched = datetime.utcnow().isoformat()

    if config.local_excel and config.local_excel.enabled:
        writer = LocalExcelWriter(
            file_path=config.local_excel.file_path,
            worksheet_name=config.local_excel.worksheet_name,
        )
        inserted, updated = writer.upsert_jobs(deduped)
        summary.total_written = inserted
        summary.total_updated = updated
    elif config.sheets:
        writer = GoogleSheetsWriter(
            spreadsheet_id=config.sheets.spreadsheet_id,
            worksheet_name=config.sheets.worksheet_name,
            credentials_path=config.sheets.credentials_path,
        )
        writer.ensure_headers()
        inserted, updated = writer.upsert_jobs(deduped)
        summary.total_written = inserted
        summary.total_updated = updated

    return summary
