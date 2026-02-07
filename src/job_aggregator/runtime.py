from __future__ import annotations

import logging
import os
from pathlib import Path

from .config import AppConfig

logger = logging.getLogger(__name__)


def _prompt_secret(prompt: str) -> str:
    try:
        from getpass import getpass

        return getpass(prompt)
    except Exception:
        return input(prompt)


def prepare_runtime_config(config: AppConfig) -> None:
    """Prompt for missing credentials and optional runtime overrides."""
    for source_name, source_cfg in config.sources.items():
        if not source_cfg.enabled or not source_cfg.api_key_env:
            continue
        if os.getenv(source_cfg.api_key_env):
            continue

        entered = _prompt_secret(
            f"Enter API key for {source_name} ({source_cfg.api_key_env}) and press Enter: "
        ).strip()
        if entered:
            os.environ[source_cfg.api_key_env] = entered
        else:
            logger.warning(
                "No API key entered for %s (%s). This source may be skipped.",
                source_name,
                source_cfg.api_key_env,
            )

    # Local Excel is preferred; when enabled we do not require Google Sheets credentials.
    if config.local_excel and config.local_excel.enabled:
        return

    if not config.sheets:
        return

    creds_path = Path(config.sheets.credentials_path)
    if creds_path.exists():
        return

    entered_path = input(
        "Google service-account JSON not found at "
        f"'{config.sheets.credentials_path}'.\n"
        "Enter a valid credentials file path (or press Enter to skip Google Sheets write): "
    ).strip()

    if entered_path and Path(entered_path).exists():
        config.sheets.credentials_path = entered_path
        return

    logger.warning("Google Sheets credentials not configured; continuing without sheet writes for this run.")
    config.sheets = None
