"""Task 1 runner. usage: python scripts/audit/t1_ablation.py --setting phi0.8 --n 1500 --procs 2"""
import argparse, os, sys, functools, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.ablation import AblCfg, ablation_study
from quantlab.audit.runner import run_resumable

SETTINGS = {
    "phi0":      AblCfg(name="phi0", phi=0.0),
    "phi0.5":    AblCfg(name="phi0.5", phi=0.5),
    "phi0.8":    AblCfg(name="phi0.8", phi=0.8),
    "phi0.95":   AblCfg(name="phi0.95", phi=0.95),
    # stochastic volatility (log-vol AR(1) rho=0.97, nu=0.25) and a series that straddles a calendar-year boundary (two year strata)
    "sv_phi0.8_2y": AblCfg(name="sv_phi0.8_2y", phi=0.8, sv=(0.97, 0.25), start="2018-07-01", hl="scaled", series_seed0=800_000),
}
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", required=True); ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--procs", type=int, default=2); ap.add_argument("--out", default="docs/audit/raw")
    ap.add_argument("--budget", type=float, default=None); ap.add_argument("--which", default="main")
    a = ap.parse_args()
    cfg = SETTINGS[a.setting]
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, f"t1_{cfg.name}.config.json"), "w") as f:
        json.dump(cfg.__dict__, f, indent=1, default=str)
    suffix = "" if a.which == "main" else "_" + a.which
    run_resumable(os.path.join(a.out, f"t1{suffix}_{cfg.name}.csv"), functools.partial(ablation_study, cfg, which=a.which), range(a.n), a.procs, block=100, time_budget=a.budget)
