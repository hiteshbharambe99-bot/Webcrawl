from __future__ import annotations

import re
import string
from dataclasses import asdict
from difflib import SequenceMatcher
from urllib.parse import urlparse

from .models import JobListing

AUS_TOKENS = {
    "australia",
    "nsw",
    "vic",
    "qld",
    "wa",
    "sa",
    "tas",
    "act",
    "nt",
    "sydney",
    "melbourne",
    "brisbane",
    "perth",
    "adelaide",
    "canberra",
    "hobart",
    "darwin",
    "gold coast",
    "newcastle",
    "wollongong",
    "geelong",
}

STOP_WORDS = {
    "senior",
    "jr",
    "junior",
    "pty",
    "ltd",
    "the",
    "and",
    "a",
    "an",
}


def normalize_text(value: str) -> str:
    cleaned = value.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = [token for token in cleaned.split() if token not in STOP_WORDS]
    return " ".join(tokens).strip()


def stable_url_component(url: str) -> str:
    parsed = urlparse(url)
    path = re.sub(r"/+$", "", parsed.path)
    path = re.sub(r"/[0-9]{4,}", "", path)
    return f"{parsed.netloc}{path}" if parsed.netloc else ""


def build_canonical_key(job: JobListing) -> str:
    title = normalize_text(job.job_title)
    company = normalize_text(job.company)
    location = normalize_text(job.location)
    unique = job.job_id or stable_url_component(job.job_url)
    return "|".join([title, company, location, unique])


def similarity_score(left: JobListing, right: JobListing) -> float:
    basis_left = "|".join(
        [
            normalize_text(left.job_title),
            normalize_text(left.company),
            normalize_text(left.location),
        ]
    )
    basis_right = "|".join(
        [
            normalize_text(right.job_title),
            normalize_text(right.company),
            normalize_text(right.location),
        ]
    )
    return SequenceMatcher(None, basis_left, basis_right).ratio()


def is_australia_job(job: JobListing) -> bool:
    haystack = " ".join(
        [job.location, job.description_snippet, job.job_title, job.work_type]
    ).lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", haystack)
    if re.search(r"\bau\b", normalized):
        return True
    return any(token in normalized for token in AUS_TOKENS)


def parse_salary(raw_text: str) -> tuple[float | None, float | None, str, str]:
    if not raw_text:
        return None, None, "AUD", ""

    text = raw_text.lower().replace(",", "")
    period = ""
    if any(x in text for x in ["/hour", "per hour", "hourly", "hr"]):
        period = "hour"
    elif any(x in text for x in ["/day", "per day", "daily"]):
        period = "day"
    elif any(x in text for x in ["/year", "per year", "annum", "pa", "p.a"]):
        period = "year"

    matches = re.findall(r"\$?\s*(\d+(?:\.\d+)?)\s*([kK]?)", text)
    values = []
    for value, is_k in matches:
        num = float(value)
        if is_k:
            num *= 1000
        values.append(num)

    if not values:
        return None, None, "AUD", period
    if len(values) == 1:
        return values[0], values[0], "AUD", period
    return min(values), max(values), "AUD", period


def to_sheet_row(job: JobListing) -> list[str]:
    data = asdict(job)
    ordered = []
    for key in [
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
    ]:
        value = data.get(key, "")
        ordered.append("" if value is None else str(value))
    return ordered
