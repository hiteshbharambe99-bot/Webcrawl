import os
from pathlib import Path

from job_aggregator.config import AppConfig, GoogleSheetsConfig, SearchConfig, SourceConfig
from job_aggregator.runtime import prepare_runtime_config


def build_cfg(tmp_path: Path) -> AppConfig:
    return AppConfig(
        search=SearchConfig(keywords=["Data Analyst"], locations=["Australia"]),
        sources={
            "Indeed": SourceConfig(enabled=True, provider="serpapi", api_key_env="SERPAPI_API_KEY")
        },
        sheets=GoogleSheetsConfig(
            spreadsheet_id="sheet-id",
            worksheet_name="Jobs_AU",
            credentials_path=str(tmp_path / "missing.json"),
        ),
    )


def test_prepare_runtime_prompts_for_api_key(monkeypatch, tmp_path):
    cfg = build_cfg(tmp_path)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    monkeypatch.setattr("job_aggregator.runtime._prompt_secret", lambda _: "abc123")
    monkeypatch.setattr("builtins.input", lambda _: "")

    prepare_runtime_config(cfg)
    assert os.getenv("SERPAPI_API_KEY") == "abc123"


def test_prepare_runtime_disables_sheets_when_missing_credentials(monkeypatch, tmp_path):
    cfg = build_cfg(tmp_path)
    monkeypatch.setenv("SERPAPI_API_KEY", "abc123")
    monkeypatch.setattr("builtins.input", lambda _: "")

    prepare_runtime_config(cfg)
    assert cfg.sheets is None


def test_prepare_runtime_accepts_override_credentials_path(monkeypatch, tmp_path):
    cfg = build_cfg(tmp_path)
    cred_file = tmp_path / "service_account.json"
    cred_file.write_text("{}")

    monkeypatch.setenv("SERPAPI_API_KEY", "abc123")
    monkeypatch.setattr("builtins.input", lambda _: str(cred_file))

    prepare_runtime_config(cfg)
    assert cfg.sheets is not None
    assert cfg.sheets.credentials_path == str(cred_file)
