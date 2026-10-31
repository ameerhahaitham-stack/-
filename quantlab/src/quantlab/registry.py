"""Append-only, hash-chained registry of hypotheses, trials, verdicts and HOLD accesses.

Lifecycle of a hypothesis
  registered --(freeze)--> frozen --(verdict valid_pass)--> valid_pass --(request_hold)--> hold_opened
  frozen --(verdict valid_fail)--> valid_fail   (terminal: archived as failure)
- DEV trials (parameter exploration) are only allowed while 'registered'.
- VALID trials are only allowed while 'frozen', and only for the exact configs that were frozen.
- HOLD is opened once per hypothesis, only after valid_pass, and every access is logged.
- Trials are refused until the protocol is locked, and refused if the protocol files changed after locking.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import root


class RegistryError(RuntimeError):
    pass


class ProtocolNotLocked(RegistryError):
    pass


class ProtocolModified(RegistryError):
    pass


def _events_path() -> Path:
    return root() / "registry" / "events.jsonl"


def _lock_path() -> Path:
    return root() / "registry" / "PROTOCOL.lock"


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def cfg_hash(cfg: dict) -> str:
    return hashlib.sha256(canon(cfg).encode()).hexdigest()[:16]


def protocol_fingerprint() -> str:
    h = hashlib.sha256()
    for rel in ["protocol/RESEARCH_PROTOCOL.md", "protocol/protocol_params.json"]:
        h.update((root() / rel).read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def lock_protocol(note: str = "") -> dict:
    if _lock_path().exists():
        raise RegistryError("protocol is already locked (it cannot be re-locked; create a new project version instead)")
    _lock_path().parent.mkdir(parents=True, exist_ok=True)
    info = {"fingerprint": protocol_fingerprint(), "locked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": note}
    _lock_path().write_text(json.dumps(info, indent=2), encoding="utf-8")
    _append({"type": "protocol_locked", "fingerprint": info["fingerprint"]})
    return info


def check_lock() -> None:
    if not _lock_path().exists():
        raise ProtocolNotLocked("research protocol is not locked yet - run: python -m quantlab.cli lock-protocol")
    info = json.loads(_lock_path().read_text(encoding="utf-8"))
    if info["fingerprint"] != protocol_fingerprint():
        raise ProtocolModified("protocol files changed after locking - results are no longer valid under the registered protocol")


def lock_status() -> dict:
    if not _lock_path().exists():
        return {"locked": False}
    info = json.loads(_lock_path().read_text(encoding="utf-8"))
    return {"locked": True, "intact": info["fingerprint"] == protocol_fingerprint(), **info}


# --------------------------------------------------------------------------- event log
def read_events() -> list[dict]:
    p = _events_path()
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(event: dict) -> dict:
    p = _events_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    evs = read_events()
    prev = evs[-1]["hash"] if evs else "GENESIS"
    ev = {"seq": len(evs) + 1, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event, "prev": prev}
    ev["hash"] = hashlib.sha256((prev + canon(ev)).encode()).hexdigest()
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
    return ev


def verify_chain() -> tuple[bool, str]:
    prev = "GENESIS"
    for ev in read_events():
        body = {k: v for k, v in ev.items() if k != "hash"}
        if body["prev"] != prev or hashlib.sha256((prev + canon(body)).encode()).hexdigest() != ev["hash"]:
            return False, f"chain broken at seq {ev['seq']}"
        prev = ev["hash"]
    return True, "ok"


# --------------------------------------------------------------------------- hypotheses
def state(hid: str) -> dict:
    st = {"exists": False, "status": None, "frozen_cfgs": [], "hold_opened": False, "hold_cfgs_used": []}
    for ev in read_events():
        if ev.get("hid") != hid:
            continue
        t = ev["type"]
        if t == "hypothesis_registered":
            st.update(exists=True, status="registered", family=ev["family"], description=ev["description"])
        elif t == "hypothesis_frozen":
            st.update(status="frozen", frozen_cfgs=ev["cfg_hashes"])
        elif t == "verdict" and ev["stage"] == "valid":
            st["status"] = "valid_pass" if ev["passed"] else "valid_fail"
        elif t == "hold_access":
            st.update(status="hold_opened", hold_opened=True)
        elif t == "trial" and ev["split"] == "hold":
            st["hold_cfgs_used"].append(ev["cfg_hash"])
    return st


def register_hypothesis(hid: str, family: str, description: str, rules: dict | None = None) -> dict:
    check_lock()
    if state(hid)["exists"]:
        raise RegistryError(f"hypothesis {hid} already exists - create a new id for a new variant")
    return _append({"type": "hypothesis_registered", "hid": hid, "family": family, "description": description, "rules": rules or {}})


def freeze_hypothesis(hid: str, configs: list[dict]) -> dict:
    """configs: list of {symbol, tf, params}. After this, only these exact configs can be validated."""
    check_lock()
    st = state(hid)
    if st["status"] != "registered":
        raise RegistryError(f"{hid}: can only freeze from 'registered' (now {st['status']})")
    return _append({"type": "hypothesis_frozen", "hid": hid, "configs": configs, "cfg_hashes": [cfg_hash(c) for c in configs]})


def record_verdict(hid: str, stage: str, passed: bool, detail: dict | None = None) -> dict:
    check_lock()
    st = state(hid)
    if stage == "valid" and st["status"] != "frozen":
        raise RegistryError(f"{hid}: valid verdict needs status 'frozen' (now {st['status']})")
    return _append({"type": "verdict", "hid": hid, "stage": stage, "passed": bool(passed), "detail": detail or {}})


def log_trial(hid: str, symbol: str, tf: str, split: str, params: dict, metrics: dict, data_source: str,
              note: str = "", synthetic: bool = False) -> dict:
    """One trial = one (hypothesis, symbol, timeframe, parameter set, split) evaluation."""
    check_lock()
    if synthetic and os.environ.get("QUANTLAB_ALLOW_SYNTH") != "1":
        raise RegistryError("synthetic data can never be logged as research")
    st = state(hid)
    if not st["exists"]:
        raise RegistryError(f"unknown hypothesis {hid} - register it first")
    cfg = {"symbol": symbol, "tf": tf, "params": params}
    h = cfg_hash(cfg)
    if split == "dev" and st["status"] != "registered":
        raise RegistryError(f"{hid}: DEV exploration is closed once frozen (status {st['status']})")
    if split == "valid":
        if st["status"] != "frozen":
            raise RegistryError(f"{hid}: VALID needs status 'frozen' (now {st['status']})")
        if h not in st["frozen_cfgs"]:
            raise RegistryError(f"{hid}: this config was not frozen - parameters cannot change after seeing VALID")
    if split == "hold":
        assert_hold_available(hid, symbol, tf, params)
    return _append({"type": "trial", "hid": hid, "family": st.get("family"), "symbol": symbol, "tf": tf, "split": split,
                    "cfg_hash": h, "params": params, "metrics": metrics, "data_source": data_source, "note": note})


def request_hold(hid: str) -> list[dict]:
    """Open HOLD for a hypothesis. One-shot and audited."""
    check_lock()
    st = state(hid)
    if st["hold_opened"]:
        raise RegistryError(f"{hid}: HOLD was already opened once - it cannot be reused")
    if st["status"] != "valid_pass":
        raise RegistryError(f"{hid}: HOLD needs status 'valid_pass' (now {st['status']})")
    cfgs = [ev["configs"] for ev in read_events() if ev["type"] == "hypothesis_frozen" and ev["hid"] == hid][-1]
    _append({"type": "hold_access", "hid": hid, "configs": cfgs})
    return cfgs


def assert_hold_available(hid: str, symbol: str, tf: str, params: dict) -> None:
    """HOLD is open for this hypothesis, the config is frozen, and this exact config has not been run on HOLD yet."""
    h = cfg_hash({"symbol": symbol, "tf": tf, "params": params})
    assert_hold_open(hid, symbol, tf, cfg_hash_=h)
    if h in state(hid)["hold_cfgs_used"]:
        raise RegistryError(f"{hid}: this config was already evaluated on HOLD - HOLD results are never re-run")


def assert_hold_open(hid: str, symbol: str, tf: str, cfg_hash_: str | None = None) -> None:
    st = state(hid)
    if not st["hold_opened"]:
        raise RegistryError(f"{hid}: HOLD is not open - call registry.request_hold('{hid}') (allowed only after valid_pass)")
    cfgs = [ev["configs"] for ev in read_events() if ev["type"] == "hypothesis_frozen" and ev["hid"] == hid][-1]
    if (symbol, tf) not in {(c["symbol"], c["tf"]) for c in cfgs}:
        raise RegistryError(f"{hid}: {symbol} {tf} is not part of the frozen configs")
    if cfg_hash_ is not None and cfg_hash_ not in st["frozen_cfgs"]:
        raise RegistryError(f"{hid}: HOLD may only run the frozen configs")


# --------------------------------------------------------------------------- queries
def trials_df() -> pd.DataFrame:
    rows = []
    for ev in read_events():
        if ev["type"] == "trial":
            m = ev.get("metrics", {})
            rows.append({"seq": ev["seq"], "ts": ev["ts"], "hid": ev["hid"], "family": ev.get("family"), "symbol": ev["symbol"],
                         "tf": ev["tf"], "split": ev["split"], "n_trades": m.get("n_trades"),
                         "expectancy_R_net": m.get("expectancy_R_net"), "profit_factor_net": m.get("profit_factor_net"),
                         "p_raw": m.get("p_raw"), "params": canon(ev["params"]), "note": ev.get("note", "")})
    return pd.DataFrame(rows)


def trial_count(splits=("dev", "valid"), family: str | None = None) -> int:
    df = trials_df()
    if df.empty:
        return 0
    df = df[df["split"].isin(splits)]
    if family:
        df = df[df["family"] == family]
    return int(len(df))


def hypotheses_df() -> pd.DataFrame:
    ids = [ev["hid"] for ev in read_events() if ev["type"] == "hypothesis_registered"]
    rows = []
    for hid in ids:
        s = state(hid)
        rows.append({"hid": hid, "family": s.get("family"), "status": s["status"], "description": s.get("description"),
                     "frozen_configs": len(s["frozen_cfgs"])})
    return pd.DataFrame(rows)
