"""Adds the exact circular-shift reference p (p_shift) to the earlier full-production G studies (docs/calibration_raw/tail_phi*.csv) by regenerating
the same series/events (same seeds). Verifies the regenerated observed statistic equals the stored one."""
import argparse, os, sys, functools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.tail import TailAudit, make_study, shift_p_exact
from quantlab.audit.runner import run_resumable

OLD = {}


def one(cfg, k):
    df, t, el, window, raw, idx, fb, pres, s0 = make_study(cfg, k)
    obs = float(raw[idx].mean())
    assert abs(obs - OLD[cfg.phi][k]) < 1e-9, (k, obs, OLD[cfg.phi][k])
    return [{"k": k, "p_shift": shift_p_exact(raw, idx, int(window[0]), int(window[-1]), obs)}]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--phi", type=float, required=True); ap.add_argument("--procs", type=int, default=2)
    a = ap.parse_args()
    old = pd.read_csv(f"docs/calibration_raw/tail_phi{a.phi}.csv")
    OLD[a.phi] = dict(zip(old.k, old.obs))
    cfg = TailAudit(phi=a.phi, mode="G")
    run_resumable(f"docs/audit/raw/t3_shiftfill_G_phi{a.phi}.csv", functools.partial(one, cfg), list(old.k), a.procs, block=1000)
