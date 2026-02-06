# AU Job Aggregator (Compliant Sources)

Collects Australian jobs from Seek, Indeed, Jora, Google Jobs, and LinkedIn using compliant access (API/provider feeds only), deduplicates results, and upserts into Google Sheets.

## Features
- Source adapters with compliance-first behavior:
  - Indeed/Jora/Google Jobs/LinkedIn via SerpAPI.
  - Seek skipped unless a compliant partner API/feed is configured.
- Filters to AU-only jobs.
- Salary parsing (range/single value), with fallback to `Not listed` when unavailable.
- Canonical and fuzzy dedupe across sources.
- Google Sheets upsert by `canonical_key`.
- Retry with exponential backoff and per-source run summary.
- CLI-ready for local runs, cron, GitHub Actions, or Cloud Run.

## Project structure

```
src/job_aggregator/
  cli.py
  config.py
  models.py
  pipeline.py
  sheets.py
  utils.py
  sources/
    base.py
    seek_source.py
    serpapi_source.py
tests/
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
3. Set your sheet destination in `config.yml` under `sheets`:
   ```yaml
   sheets:
     spreadsheet_id: "300411b4281dd5f8b203bc36433a58e2be11e4e337fc641e0540eb48393a090a"
     worksheet_name: Jobs_AU
   ```
4. Set environment variables:
   ```bash
   export SERPAPI_API_KEY=your_key
   ```
5. Configure Google Sheets credentials:
   - Create a GCP project and enable **Google Sheets API**.
   - Create a **Service Account** and download JSON key.
   - Save it at `./credentials/service_account.json` (or update `credentials_path`).
   - Share your target spreadsheet with the service account email as Editor.
   - Set `sheets.spreadsheet_id` to `300411b4281dd5f8b203bc36433a58e2be11e4e337fc641e0540eb48393a090a` and tab to `Jobs_AU`.

## Run
```bash
PYTHONPATH=src python -m job_aggregator.cli --config config.yml
```

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
