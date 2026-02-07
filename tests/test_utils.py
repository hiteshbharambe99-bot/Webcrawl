from job_aggregator.models import JobListing
from job_aggregator.pipeline import dedupe_jobs
from job_aggregator.utils import build_canonical_key, is_australia_job, parse_salary


def test_parse_salary_k_range():
    mn, mx, curr, period = parse_salary("$90k-$110k per year")
    assert mn == 90000
    assert mx == 110000
    assert curr == "AUD"
    assert period == "year"


def test_parse_salary_not_listed():
    mn, mx, _, _ = parse_salary("Competitive")
    assert mn is None
    assert mx is None


def test_canonical_key_normalization():
    job = JobListing(
        source="Indeed",
        job_title="Senior Data Analyst",
        company="Example Pty Ltd",
        location="Melbourne, VIC",
        job_url="https://example.com/jobs/12345",
        job_id="",
    )
    key = build_canonical_key(job)
    assert key.startswith("data analyst|example|melbourne vic|")


def test_dedupe_logic_prefers_salary():
    a = JobListing(source="Indeed", job_title="Data Analyst", company="ACME", location="Sydney NSW", salary_raw_text="Not listed")
    b = JobListing(source="Jora", job_title="Data Analyst", company="ACME", location="Sydney, NSW", salary_min=100000, salary_max=120000, salary_raw_text="$100k-$120k")
    deduped = dedupe_jobs([a, b], threshold=0.9)
    assert len(deduped) == 1
    assert deduped[0].salary_min == 100000


def test_au_location_filtering():
    au_job = JobListing(source="Indeed", job_title="Engineer", company="X", location="Perth WA")
    non_au_job = JobListing(source="Indeed", job_title="Engineer", company="X", location="Auckland NZ")
    assert is_australia_job(au_job)
    assert not is_australia_job(non_au_job)
