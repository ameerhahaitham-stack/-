"""Data validator, sealing of HOLD, registry lifecycle and tamper detection."""
import json

import numpy as np
import pandas as pd
import pytest

from quantlab import data, registry, synth
from quantlab.config import load_config, root


def _m15(sym="EURUSD", start="2018-01-01", end="2018-04-30"):
    return synth.make_m15(sym, start, end, seed=1)


# ----------------------------------------------------------------- validator
def test_clean_synthetic_data_passes_all_checks(lab):
    m15 = _m15()
    for tf in ["M15", "H1", "H4", "D1"]:
        rep = data.validate(synth.aggregate(m15, tf), "EURUSD", tf)
        assert rep["status"] in ("PASS", "WARN"), [c for c in rep["checks"] if c["status"] == "FAIL"]
        fails = [c for c in rep["checks"] if c["status"] == "FAIL"]
        assert not fails


def test_validator_detects_injected_defects(lab):
    h1 = synth.aggregate(_m15(), "H1")
    dup = pd.concat([h1, h1.iloc[[100, 101]]]).sort_values("time", kind="mergesort").reset_index(drop=True)
    assert next(c for c in data.validate(dup, "EURUSD", "H1")["checks"] if c["name"] == "duplicates")["status"] == "FAIL"
    bad = h1.copy()
    bad.loc[50, "high"] = bad.loc[50, "low"] - 0.01
    assert next(c for c in data.validate(bad, "EURUSD", "H1")["checks"] if c["name"] == "ohlc_valid")["status"] == "FAIL"
    day = h1["time"].dt.normalize().iloc[300]
    holed = h1[h1["time"].dt.normalize() != day].reset_index(drop=True)
    g = next(c for c in data.validate(holed, "EURUSD", "H1")["checks"] if c["name"] == "gaps")
    assert g["status"] in ("WARN", "FAIL") and "unexpected missing bars" in g["detail"]
    spike = h1.copy()
    spike.loc[200, ["open", "high", "low", "close"]] = spike.loc[200, "close"] * 1.2
    assert next(c for c in data.validate(spike, "EURUSD", "H1")["checks"] if c["name"] == "price_jumps")["status"] == "FAIL"


def test_cross_timeframe_check_passes_consistent_and_flags_corrupt(lab):
    m15 = _m15()
    h1, h4 = synth.aggregate(m15, "H1"), synth.aggregate(m15, "H4")
    assert data.cross_check(h1, h4, "H1", "H4")["status"] == "PASS"
    assert data.cross_check(m15, h1, "M15", "H1")["status"] == "PASS"
    bad = h4.copy()
    bad.loc[::3, "high"] = bad.loc[::3, "high"] * 1.01
    assert data.cross_check(h1, bad, "H1", "H4")["status"] == "FAIL"


def test_week_open_shift_is_reported(lab):
    h1 = synth.aggregate(_m15(start="2018-01-01", end="2018-12-31"), "H1")
    shifted = h1.copy()
    mask = shifted["time"] >= "2018-07-01"
    shifted.loc[mask, "time"] = shifted.loc[mask, "time"] + pd.Timedelta(hours=1)   # server clock moved by one hour mid-year
    chk = next(c for c in data.validate(shifted, "EURUSD", "H1")["checks"] if c["name"] == "week_open_pattern")
    assert chk["status"] == "WARN" and "2018" in chk["detail"]


# ----------------------------------------------------------------- ingest / sealing
def _ingest_synth(lab, syms=("EURUSD",), tfs=("D1", "H4")):
    synth.make_all(root() / "data" / "incoming", symbols=syms, start="2018-01-01", end="2019-12-31", tfs=tfs)
    for s in syms:
        for tf in tfs:
            data.ingest(root() / "data" / "incoming" / f"SYNTH_{s}_{tf}.csv", s, tf, "synthetic test data", synthetic=True)


def test_hold_is_physically_separated_and_loader_refuses_it(lab):
    _ingest_synth(lab)
    dev, es, ee, _ = data.load_with_context("EURUSD", "D1", "dev")
    assert dev["time"].max() < pd.Timestamp("2019-01-01")
    val, es2, ee2, _ = data.load_with_context("EURUSD", "D1", "valid")
    assert val["time"].max() < pd.Timestamp("2019-07-01") and es2 == pd.Timestamp("2019-01-01")
    assert (root() / "data" / "sealed" / "EURUSD_D1_hold.csv.gz").exists()
    for f in (root() / "data" / "clean").glob("*.gz"):
        assert "hold" not in f.name
    with pytest.raises(data.HoldLockedError):
        data.load_with_context("EURUSD", "D1", "hold")
    with pytest.raises(registry.RegistryError):
        data.load_with_context("EURUSD", "D1", "hold", hid="H_nope")


def test_modified_clean_file_is_detected(lab):
    _ingest_synth(lab)
    p = root() / "data" / "clean" / "EURUSD_D1_dev.csv.gz"
    df = pd.read_csv(p)
    df.loc[5, "close"] += 0.001
    df.to_csv(p, index=False, compression="gzip")
    with pytest.raises(data.DataIntegrityError):
        data.load_with_context("EURUSD", "D1", "dev")


def test_changing_splits_after_ingest_is_blocked(lab):
    _ingest_synth(lab)
    pp = json.loads((root() / "protocol" / "protocol_params.json").read_text())
    pp["splits"]["dev"]["end"] = "2018-11-30"
    (root() / "protocol" / "protocol_params.json").write_text(json.dumps(pp))
    with pytest.raises(data.DataIntegrityError):
        data.load_with_context("EURUSD", "D1", "dev")


def test_clean_logs_and_never_fills_gaps(lab):
    h1 = synth.aggregate(_m15(), "H1")
    broken = pd.concat([h1, h1.iloc[[10]]]).reset_index(drop=True)
    broken.loc[20, "low"] = broken.loc[20, "high"] + 1
    c, q, log = data.clean(broken)
    assert log["duplicates_dropped"] == 1 and log["quarantined_invalid_ohlc"] == 1 and len(q) == 1
    assert len(c) == len(h1) - 1


# ----------------------------------------------------------------- registry
def test_trials_refused_until_protocol_locked_and_after_modification(lab):
    with pytest.raises(registry.ProtocolNotLocked):
        registry.register_hypothesis("H1", "fam", "x")
    registry.lock_protocol()
    registry.register_hypothesis("H1", "fam", "x")
    (root() / "protocol" / "RESEARCH_PROTOCOL.md").write_text("changed after lock")
    with pytest.raises(registry.ProtocolModified):
        registry.log_trial("H1", "EURUSD", "D1", "dev", {}, {}, "src")


def test_lifecycle_freeze_valid_hold_rules(lab):
    registry.lock_protocol()
    registry.register_hypothesis("H2", "fam", "d")
    cfg = {"symbol": "EURUSD", "tf": "D1", "params": {"n": 20}}
    registry.log_trial("H2", "EURUSD", "D1", "dev", {"n": 20}, {"n_trades": 10}, "src")
    registry.log_trial("H2", "EURUSD", "D1", "dev", {"n": 30}, {"n_trades": 12}, "src")
    with pytest.raises(registry.RegistryError):                # VALID before freeze
        registry.log_trial("H2", "EURUSD", "D1", "valid", {"n": 20}, {}, "src")
    registry.freeze_hypothesis("H2", [cfg])
    with pytest.raises(registry.RegistryError):                # DEV exploration closed after freeze
        registry.log_trial("H2", "EURUSD", "D1", "dev", {"n": 40}, {}, "src")
    with pytest.raises(registry.RegistryError):                # parameters cannot change after seeing VALID
        registry.log_trial("H2", "EURUSD", "D1", "valid", {"n": 25}, {}, "src")
    registry.log_trial("H2", "EURUSD", "D1", "valid", {"n": 20}, {"n_trades": 8}, "src")
    with pytest.raises(registry.RegistryError):                # HOLD needs valid_pass
        registry.request_hold("H2")
    registry.record_verdict("H2", "valid", True)
    registry.request_hold("H2")
    with pytest.raises(registry.RegistryError):                # one-shot
        registry.request_hold("H2")
    registry.log_trial("H2", "EURUSD", "D1", "hold", {"n": 20}, {"n_trades": 4}, "src")
    with pytest.raises(registry.RegistryError):                # HOLD only for frozen configs
        registry.log_trial("H2", "EURUSD", "D1", "hold", {"n": 99}, {}, "src")


def test_failed_hypothesis_can_never_open_hold(lab):
    registry.lock_protocol()
    registry.register_hypothesis("H3", "fam", "d")
    registry.freeze_hypothesis("H3", [{"symbol": "EURUSD", "tf": "D1", "params": {}}])
    registry.record_verdict("H3", "valid", False)
    with pytest.raises(registry.RegistryError):
        registry.request_hold("H3")


def test_hash_chain_detects_edited_history(lab):
    registry.lock_protocol()
    registry.register_hypothesis("H4", "fam", "d")
    registry.log_trial("H4", "EURUSD", "D1", "dev", {}, {"n_trades": 10, "expectancy_R_net": -0.2}, "src")
    assert registry.verify_chain()[0]
    p = root() / "registry" / "events.jsonl"
    lines = p.read_text().splitlines()
    lines[-1] = lines[-1].replace("-0.2", "0.9")
    p.write_text("\n".join(lines) + "\n")
    assert not registry.verify_chain()[0]


def test_synthetic_data_refused_as_research_without_override(lab, monkeypatch):
    registry.lock_protocol()
    registry.register_hypothesis("H5", "fam", "d")
    monkeypatch.delenv("QUANTLAB_ALLOW_SYNTH")
    with pytest.raises(registry.RegistryError):
        registry.log_trial("H5", "EURUSD", "D1", "dev", {}, {}, "synthetic", synthetic=True)
