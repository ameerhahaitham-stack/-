"""Supplementary audit T10: drift-regime null for the combination monthly-bootstrap gate x matched-control gate. Strategy = random-timing, ALWAYS-LONG signals (no skill) on
synthetic series with a persistent zero-mean two-state drift. usage: python scripts/audit/t10_drift.py --setting D1 --n 240 --procs 1"""
import argparse, os, sys, functools, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.tradecal import DriftCfg, drift_study
from quantlab.audit.runner import run_resumable

SETTINGS = {"D0": DriftCfg(name="D0", mu=0.0), "D1": DriftCfg(name="D1", mu=0.3), "D2": DriftCfg(name="D2", mu=0.6)}
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", required=True); ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--procs", type=int, default=1); ap.add_argument("--out", default="docs/audit/raw"); ap.add_argument("--budget", type=float, default=None)
    a = ap.parse_args(); cfg = SETTINGS[a.setting]; os.makedirs(a.out, exist_ok=True)
    json.dump(cfg.__dict__, open(os.path.join(a.out, f"t10_{cfg.name}.config.json"), "w"), indent=1)
    run_resumable(os.path.join(a.out, f"t10_{cfg.name}.csv"), functools.partial(drift_study, cfg), range(a.n), a.procs, block=20, time_budget=a.budget)
