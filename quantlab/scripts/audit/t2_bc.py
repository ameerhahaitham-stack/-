"""Task 2 runner: Besag-Clifford conditional-uniform reference p (p_bc) on the SAME studies (series/event seeds) as scripts/audit/t3_tail.py.
usage: python scripts/audit/t2_bc.py --mode G --phi 0.8 --n 20000 [--k0 0]"""
import argparse, os, sys, functools, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit import sampler as S
from quantlab.audit.bc import bc_pvalue
from quantlab.audit.runner import run_resumable
from quantlab.audit.tail import TailAudit, make_study

M_PRE, M_FULL, THIN_MULT, PRE_CUT = 2000, 20000, 2, 0.02


def bc_study(cfg, nfull, k0, k):
    df, t, el, window, raw, idx, fb, preserved, s0 = make_study(cfg, k)
    lo, hi = 60, cfg.n_bars - 50
    # chain support = the support of the null event process: for mode G the domain [60, n-50) (events never occur elsewhere); for modes S/C/R the same
    dom = window if cfg.mode == "W" else window[(window >= lo) & (window < hi)]
    pf = S.pool_function(df, dom, "full")
    pools = [pf(i) for i in idx]
    rng = np.random.default_rng(cfg.ref_seed0 + 3_000_000 + k)
    p_pre, obs, _ = bc_pvalue(idx, pools, raw, cfg.n_bars, cfg.min_gap, M_PRE, THIN_MULT * len(idx), rng)
    p_full = float("nan")
    if (k0 <= k < k0 + nfull) or p_pre <= PRE_CUT:
        p_full, _, _ = bc_pvalue(idx, pools, raw, cfg.n_bars, cfg.min_gap, M_FULL, THIN_MULT * len(idx), np.random.default_rng(cfg.ref_seed0 + 4_000_000 + k))
    return [{"k": k, "n_events": len(idx), "obs": obs, "p_bc_pre": p_pre, "p_bc": p_full, "tier": int(not np.isnan(p_full))}]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True); ap.add_argument("--phi", type=float, required=True)
    ap.add_argument("--n", type=int, default=10000); ap.add_argument("--k0", type=int, default=0); ap.add_argument("--nfull", type=int, default=3000)
    ap.add_argument("--procs", type=int, default=2); ap.add_argument("--out", default="docs/audit/raw"); ap.add_argument("--budget", type=float, default=None)
    a = ap.parse_args()
    cfg = TailAudit(phi=a.phi, mode=a.mode)
    os.makedirs(a.out, exist_ok=True)
    name = f"t2bc_{a.mode}_phi{a.phi}"
    json.dump({**cfg.__dict__, "M_PRE": M_PRE, "M_FULL": M_FULL, "THIN": f"{THIN_MULT}*k", "PRE_CUT": PRE_CUT}, open(os.path.join(a.out, name + ".config.json"), "w"), indent=1)
    run_resumable(os.path.join(a.out, name + ".csv"), functools.partial(bc_study, cfg, a.nfull, a.k0), range(a.k0, a.k0 + a.n), a.procs, block=250, time_budget=a.budget)
