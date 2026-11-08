"""Task 3 (family of 82): full-null, mixed (true + null) and staged-selection simulations of the production Holm step, with dependence between hypotheses.
Holm is applied EXACTLY as registry.family_table does: m = 82 for the whole family, trials without a p keep p = 1 (padding), p_raw of strategies from the
production cluster bootstrap (fixed seed 12345 => common resampling indices) -- reimplemented byte-for-byte (tests/test_audit_bootstrap_equiv.py).
Also verifies Holm itself independently (own implementation vs stats.holm; FWER with EXACTLY valid p under dependence).
usage: python scripts/audit/t4d_family.py --part holmcheck|mixed [--fams 2500]"""
import argparse, os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootcal import Scenario, simulate_family, family_pvals
from quantlab.stats import holm
from scipy.stats import norm
from multiprocessing import Pool

SEED0 = 20261111
M = 82
SC = {"A2_iid_rr2": Scenario("A2", r_dist="rr2"), "B1_ar0.3_rr2": Scenario("B1", r_dist="rr2", phi_trade=0.3),
      "C3_month_eff0.5_ar0.8": Scenario("C3", r_dist="rr2", month_effect=0.5, phi_month=0.8)}


def my_holm(p, m):
    """independent step-down Holm: sorted p_(i) * (m - i + 1), cumulative max, capped at 1 (i = 1..n; the other m-n hypotheses carry p=1)."""
    p = np.asarray(p, float); o = np.argsort(p, kind="stable"); adj = np.empty(len(p))
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(run, 1.0)
    return adj


def holmcheck(_):
    rng = np.random.default_rng(SEED0)
    mism = 0
    for _ in range(3000):
        n = int(rng.integers(1, M + 1)); p = rng.random(n) ** rng.integers(1, 6)
        if np.abs(my_holm(p, M) - holm(p, M)).max() > 1e-12:
            mism += 1
    out = {"implementation_mismatches_vs_stats.holm(3000 random vectors, padding m=82)": mism}
    for rho in (0.0, 0.5, 0.9, 0.99):
        fw = 0; S = 20000
        for _ in range(S):
            z = np.sqrt(rho) * rng.normal() + np.sqrt(1 - rho) * rng.normal(size=M)
            p = norm.sf(z)                                    # EXACTLY uniform marginals, Gaussian-copula dependence
            fw += (holm(p, M) <= 0.10).any()
        out[f"FWER_exact_valid_p_rho{rho}"] = fw / S
    return out


def fam(args):
    name, rho, n_true, delta, staged, ci, nfam = args
    sc = SC[name]
    rng = np.random.default_rng([SEED0, 5, list(SC).index(name), int(rho * 100), n_true, int(staged), ci])
    res = np.zeros((nfam, 9))
    for j in range(nfam):
        r, mid = simulate_family(sc, M, rho, rng)
        true = np.zeros(M, bool); true[:n_true] = True
        r = r + delta * true[:, None]
        if staged:                                           # DEV screen on DEV data, then VALID on FRESH data for the selected only
            sel = r.mean(axis=1) > 0
            r2, mid2 = simulate_family(sc, M, rho, rng)
            r2 = r2 + delta * true[:, None]
            p = np.ones(M)
            if sel.any():
                p[sel] = family_pvals(r2[sel], mid2, common_idx=True)
        else:
            sel = np.ones(M, bool); p = family_pvals(r, mid, common_idx=True)
        adj = np.ones(M); has = sel
        if has.any():
            adj[has] = holm(p[has], M)          # exactly family_table: missing p -> 1, m = 82
        null = ~true
        res[j] = (float((adj[null] <= 0.10).any()), (adj[null] <= 0.10).sum(), (p[null & sel] <= 0.10).sum(), (p[null & sel] <= 0.10 / M).sum(),
                  (adj[true] <= 0.10).sum(), (p[true & sel] <= 0.10 / M).sum(), sel[null].sum(), sel[true].sum(), n_true)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--part", required=True); ap.add_argument("--fams", type=int, default=2500)
    ap.add_argument("--procs", type=int, default=2); ap.add_argument("--out", default="docs/audit/raw/t4d"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.part == "holmcheck":
        r = holmcheck(0); json.dump(r, open(f"{a.out}/holm_independent_check.json", "w"), indent=1); print(r)
    else:
        ch = 50
        grid = [(n, 0.5, nt, d, st) for n in SC for (nt, d, st) in ((0, 0.0, False), (5, 0.5, False), (20, 0.5, False), (5, 0.5, True), (0, 0.0, True))]
        grid += [("A2_iid_rr2", rho, nt, 0.5, False) for rho in (0.0, 0.9) for nt in (5,)]
        with Pool(a.procs) as pool:
            for (name, rho, nt, d, st) in grid:
                f = f"{a.out}/fam_{name}_rho{rho}_true{nt}_d{d}_{'staged' if st else 'full'}.npy"
                if os.path.exists(f):
                    continue
                t0 = time.time()
                res = np.vstack(pool.map(fam, [(name, rho, nt, d, st, ci, min(ch, a.fams - ci * ch)) for ci in range((a.fams + ch - 1) // ch)]))
                np.save(f, res); print(f, f"{time.time()-t0:.0f}s", flush=True)
