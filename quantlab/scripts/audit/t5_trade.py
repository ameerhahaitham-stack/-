"""Task 5 runner. usage: python scripts/audit/t5_trade.py --setting phi0.8_mid --n 1000 --procs 2"""
import argparse, os, sys, functools, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.tradecal import TradeCfg, trade_study
from quantlab.audit.runner import run_resumable

SETTINGS = {}
for phi in (0.0, 0.8, 0.95):
    SETTINGS[f"phi{phi}_sparse"] = TradeCfg(name=f"phi{phi}_sparse", phi=phi, n_raw=40, max_hold=10)
    SETTINGS[f"phi{phi}_mid"] = TradeCfg(name=f"phi{phi}_mid", phi=phi, n_raw=70, max_hold=20)
    SETTINGS[f"phi{phi}_crowded"] = TradeCfg(name=f"phi{phi}_crowded", phi=phi, n_raw=150, max_hold=40)
SETTINGS['phi0.8_regular'] = TradeCfg(name='phi0.8_regular', phi=0.8, regular=14, max_hold=30, k_atr=4.0, rr=3.0)
SETTINGS['phi0.0_regular'] = TradeCfg(name='phi0.0_regular', phi=0.0, regular=14, max_hold=30, k_atr=4.0, rr=3.0)
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", required=True); ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--procs", type=int, default=2); ap.add_argument("--out", default="docs/audit/raw"); ap.add_argument("--budget", type=float, default=None)
    a = ap.parse_args()
    cfg = SETTINGS[a.setting]
    os.makedirs(a.out, exist_ok=True)
    json.dump(cfg.__dict__, open(os.path.join(a.out, f"t5_{cfg.name}.config.json"), "w"), indent=1)
    run_resumable(os.path.join(a.out, f"t5_{cfg.name}.csv"), functools.partial(trade_study, cfg), range(a.n), a.procs, block=50, time_budget=a.budget)
