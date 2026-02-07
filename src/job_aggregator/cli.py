from __future__ import annotations

import argparse
import json
import logging

from .config import load_config
from .pipeline import run_pipeline
from .runtime import prepare_runtime_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Australia jobs aggregator")
    parser.add_argument("--config", default="config.yml", help="Path to config file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = load_config(args.config)
    prepare_runtime_config(cfg)
    summary = run_pipeline(cfg)
    print(json.dumps(summary.__dict__, indent=2, default=str))


if __name__ == "__main__":
    main()
