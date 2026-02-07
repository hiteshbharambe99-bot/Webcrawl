# AU Job Aggregator (Compliant Sources)

Collects Australian jobs from Seek, Indeed, Jora, Google Jobs, and LinkedIn using compliant access (API/provider feeds only), deduplicates results, and upserts into a local Excel file (`.xlsx`).

## Features
- Source adapters with compliance-first behavior:
  - Indeed/Jora/Google Jobs/LinkedIn via SerpAPI.
  - Seek skipped unless a compliant partner API/feed is configured.
- Filters to AU-only jobs.
- Salary parsing (range/single value), with fallback to `Not listed` when unavailable.
- Canonical and fuzzy dedupe across sources.
- Local Excel upsert by `canonical_key` (default output target).
- Retry with exponential backoff and per-source run summary.
- CLI-ready for local runs, cron, GitHub Actions, or Cloud Run.

## Project structure

```
src/job_aggregator/
  cli.py
  config.py
  excel.py
  models.py
  pipeline.py
  runtime.py
  sheets.py
  utils.py
  sources/
    base.py
    seek_source.py
    serpapi_source.py
tests/
  test_runtime.py
  test_utils.py
config.example.yml
requirements.txt
```

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy config:
   ```bash
   cp config.example.yml config.yml
   ```
3. Set local Excel destination in `config.yml`:
   ```yaml
   local_excel:
     enabled: true
     file_path: ./output/jobs_au.xlsx
     worksheet_name: Jobs_AU
   ```
4. Set environment variables (this is your **SerpAPI key**, not your spreadsheet ID):
   ```bash
   export SERPAPI_API_KEY=your_serpapi_key
   ```
   If not set, the CLI will prompt you for missing API keys at runtime.

## Run
```bash
PYTHONPATH=src python -m job_aggregator.cli --config config.yml
```

On startup, the CLI prompts for any missing source API keys.
Output is written to local Excel file: `./output/jobs_au.xlsx` (sheet/tab `Jobs_AU`).

The CLI prints a run summary:
- `total_fetched`, `total_kept_au`, `total_with_salary`, `total_deduped`, `total_written`, `total_updated`
- `source_success` and `source_fail`.

## Notes on compliance
- No brittle HTML scraping is implemented.
- If a source lacks compliant access, it is skipped and logged.
- Always ensure your provider usage complies with source ToS and robots/rate limits.

## Tests
```bash
PYTHONPATH=src pytest -q
```
