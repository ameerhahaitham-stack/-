import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def lab(tmp_path, monkeypatch):
    """Isolated project root with small split windows, so tests never touch the real registry or data."""
    r = tmp_path / "lab"
    for sub in ["config", "protocol"]:
        shutil.copytree(SRC_ROOT / sub, r / sub)
    for sub in ["data/incoming", "data/clean", "data/sealed", "data/specs", "registry", "reports/data_quality", "results", "charts"]:
        (r / sub).mkdir(parents=True, exist_ok=True)
    pp = json.loads((r / "protocol" / "protocol_params.json").read_text())
    pp["splits"] = {"dev": {"start": "2018-01-01", "end": "2018-12-31"}, "valid": {"start": "2019-01-01", "end": "2019-06-30"},
                    "hold": {"start": "2019-07-01", "end": None}}
    pp["bootstrap"]["n"] = 300
    pp["control"]["n_reps"] = 25
    pp["criteria"]["valid"]["min_trades"] = 5
    pp["criteria"]["hold"]["min_trades"] = 3
    (r / "protocol" / "protocol_params.json").write_text(json.dumps(pp))
    cfg = json.loads((r / "config" / "config.json").read_text())
    cfg["data_quality"]["min_start"] = "2018-01-31"
    (r / "config" / "config.json").write_text(json.dumps(cfg))
    monkeypatch.setenv("QUANTLAB_ROOT", str(r))
    monkeypatch.setenv("QUANTLAB_ALLOW_SYNTH", "1")
    return r


def mk(bars, spread=0.0, start="2020-01-06"):
    """bars: list of (open, high, low, close) -> DataFrame in engine format (hourly bars)."""
    t = pd.date_range(start, periods=len(bars), freq="h")
    d = pd.DataFrame(bars, columns=["open", "high", "low", "close"])
    d.insert(0, "time", t)
    d["tick_volume"] = 100
    d["spread"] = spread
    d["real_volume"] = 0
    return d
