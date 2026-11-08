"""Task 4 extras: (a) resamples needed / fixed-vs-fresh seed, (b) Holm FWER for a family of m=82 null strategies under dependence.
usage: python scripts/audit/t4b_extra.py --part a|b [--reps N] [--procs 2]"""
import argparse, os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootcal import Scenario, simulate_trades, month_sums, prod_idx, simulate_family, family_pvals
from quantlab.stats import holm
from multiprocessing import Pool

SEED0 = 20261108
NS = (1000, 5000, 20000, 100000)
SCEN = {"A2_iid_rr2": Scenario("A2", r_dist="rr2"), "B2_ar0.7_rr2": Scenario("B2", r_dist="rr2", phi_trade=0.7),
        "C3_month_eff0.5_ar0.8": Scenario("C3", r_dist="rr2", month_effect=0.5, phi_month=0.8)}


def _count_ge(sums, cnts, idx):
    means = sums[idx].sum(1) / np.maximum(cnts[idx].sum(1), 1)
    obs = sums.sum() / cnts.sum()
    return int(((means - obs) >= obs).sum())


def part_a(args):
    name, ci, nrep = args
    sc = SCEN[name]
    rng = np.random.default_rng([SEED0, list(SCEN).index(name), ci])
    out = np.zeros((nrep, len(NS) + 1), np.int64)           # counts: n=1000,5000,20000,100000 fresh seeds + n=5000 production fixed seed
    for j in range(nrep):
        r, mid = simulate_trades(sc, rng)
        s, c = month_sums(r, mid); K = len(s)
        for q, n in enumerate(NS):
            out[j, q] = _count_ge(s, c, rng.integers(0, K, size=(n, K)))
        out[j, len(NS)] = _count_ge(s, c, prod_idx(K))
    return out


def part_b(args):
    name, rho, common, ci, nfam, m = args
    sc = SCEN[name]
    rng = np.random.default_rng([SEED0, 100, list(SCEN).index(name), int(rho * 100), int(common), ci])
    res = np.zeros((nfam, 4))
    for j in range(nfam):
        r, mid = simulate_family(sc, m, rho, rng)
        p = family_pvals(r, mid, common_idx=common, rng=rng)
        adj = holm(p, m)
        res[j] = (p.min(), adj.min(), float((adj <= 0.10).any()), float((p <= 0.10 / m).sum()))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True); ap.add_argument("--reps", type=int, default=20000); ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default="docs/audit/raw/t4"); ap.add_argument("--fams", type=int, default=2500)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    with Pool(a.procs) as pool:
        if a.part == "a":
            for name in SCEN:
                f = os.path.join(a.out, f"t4a_resamples_{name}.npy")
                if os.path.exists(f):
                    continue
                t0 = time.time(); ch = 500
                res = pool.map(part_a, [(name, ci, min(ch, a.reps - ci * ch)) for ci in range((a.reps + ch - 1) // ch)])
                np.save(f, np.vstack(res)); print(name, f"{time.time()-t0:.0f}s", flush=True)
        else:
            m = 82; ch = 50
            grid = [(n, rho, True) for n in SCEN for rho in (0.0, 0.5, 0.9)] + [("A2_iid_rr2", 0.0, False), ("A2_iid_rr2", 0.9, False)]
            for (name, rho, common) in grid:
                f = os.path.join(a.out, f"t4b_holm_{name}_rho{rho}_{'common' if common else 'indep'}idx.npy")
                if os.path.exists(f):
                    continue
                t0 = time.time()
                res = pool.map(part_b, [(name, rho, common, ci, min(ch, a.fams - ci * ch), m) for ci in range((a.fams + ch - 1) // ch)])
                np.save(f, np.vstack(res)); print(name, rho, common, f"{time.time()-t0:.0f}s", flush=True)
