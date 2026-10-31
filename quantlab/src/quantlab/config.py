"""Paths and configuration. The project root is read lazily so tests can point to a temp root."""
from __future__ import annotations

import json
import os
from pathlib import Path


def root() -> Path:
    env = os.environ.get("QUANTLAB_ROOT")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def load_config() -> dict:
    return json.loads((root() / "config" / "config.json").read_text(encoding="utf-8"))


def protocol_params() -> dict:
    return json.loads((root() / "protocol" / "protocol_params.json").read_text(encoding="utf-8"))


def ensure_dirs() -> None:
    for sub in ["data/incoming", "data/clean", "data/sealed", "data/specs", "registry",
                "reports/data_quality", "results", "charts"]:
        (root() / sub).mkdir(parents=True, exist_ok=True)
