"""Task 4 (extended): why is the monthly cluster bootstrap miscalibrated? Grid over the NUMBER OF MONTHS K and several dependence structures, with
diagnostic alternatives computed on the SAME datasets:
  boot   : production p (iid month resampling, n=5000, seed 12345)
  t      : cluster-robust t on month totals, K-1 df (iid months, finite-K reference distribution)
  nw     : Newey-West (Bartlett, lag 3) t on month totals, K-1 df (serial dependence between months)
  cbb3   : circular month-BLOCK bootstrap, block length 3, same centred-null p, n=5000
  oracle : z test with the TRUE sd of the mean (sd measured over the scenario's own replications) = what an exactly-known variance would give
Also records the bootstrap's implied variance of the mean vs the true variance (design effect) and skewness.
usage: python scripts/audit/t4c_extended.py [--reps 30000]"""
import argparse, os, sys, json, time
import numpy as np
from scipy.stats import t as tdist
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootcal import Scenario, simulate_trades, month_sums, prod_idx
from multiprocessing import Pool

SEED0 = 20261110
S = Scenario
BASE = {"A2_iid_rr2": S("A2", r_dist="rr2"), "A1_iid_normal": S("A1"), "B1_ar0.3_rr2": S("B1", r_dist="rr2", phi_trade=0.3), "B2_ar0.7_rr2": S("B2", r_dist="rr2", phi_trade=0.7),
        "C3_month_eff0.5_ar0.8": S("C3", r_dist="rr2", month_effect=0.5, phi_month=0.8), "E1_streak0.9_rr2": S("E1", r_dist="rr2", streaks=0.9),
        "D2_vol1.0_rr2": S("D2", r_dist="rr2", vol_sd=1.0)}
KS = (6, 12, 18, 24, 36, 60, 120)
B, NB = 3, 5000
_CB = {}


def cbb_idx(K):
    if K not in _CB:
        rng = np.random.default_rng(777)
        nblk = -(-K // B)
        st = rng.integers(0, K, size=(NB, nblk))
        _CB[K] = ((st[:, :, None] + np.arange(B)[None, None, :]) % K).reshape(NB, -1)[:, :K]
    return _CB[K]


def one(args):
    name, K, ci, nrep = args
    sc = BASE[name].__class__(**{**BASE[name].__dict__, "K": K})
    rng = np.random.default_rng([SEED0, list(BASE).index(name), K, ci])
    out = np.full((nrep, 8), np.nan)
    for j in range(nrep):
        r, mid = simulate_trades(sc, rng)
        s, c = month_sums(r, mid); k = len(s)
        if k < 3:
            continue
        obs = s.sum() / c.sum()
        idx = prod_idx(k); m = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
        p_boot = (1 + ((m - obs) >= obs).sum()) / (NB + 1)
        u = s - obs * c; C = c.sum()
        se_t = np.sqrt(k / (k - 1) * (u ** 2).sum()) / C
        p_t = tdist.sf(obs / se_t, k - 1) if se_t > 0 else 1.0
        L = 3
        v = (u ** 2).sum() + 2 * sum((1 - l / (L + 1)) * (u[l:] * u[:-l]).sum() for l in range(1, min(L, k - 1) + 1))
        se_nw = np.sqrt(max(v, 1e-12) * k / (k - 1)) / C
        p_nw = tdist.sf(obs / se_nw, k - 1)
        ib = cbb_idx(k); mb = s[ib].sum(1) / np.maximum(c[ib].sum(1), 1)
        p_cbb = (1 + ((mb - obs) >= obs).sum()) / (NB + 1)
        out[j] = (obs, p_boot, p_t, p_nw, p_cbb, m.var(), k, len(r))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=30000); ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default="docs/audit/raw/t4c"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    json.dump({"seed0": SEED0, "reps": a.reps, "base": {k: v.__dict__ for k, v in BASE.items()}, "K": KS, "cbb_block": B, "nw_lag": 3, "n_resamples": NB}, open(f"{a.out}/t4c_config.json", "w"), indent=1)
    ch = 2500
    with Pool(a.procs) as pool:
        for name in BASE:
            for K in KS:
                f = f"{a.out}/{name}_K{K}.npz"
                if os.path.exists(f):
                    continue
                t0 = time.time()
                res = np.vstack(pool.map(one, [(name, K, ci, min(ch, a.reps - ci * ch)) for ci in range((a.reps + ch - 1) // ch)]))
                np.savez_compressed(f, obs=res[:, 0], p_boot=res[:, 1], p_t=res[:, 2], p_nw=res[:, 3], p_cbb3=res[:, 4], boot_var=res[:, 5], n_clusters=res[:, 6], n_trades=res[:, 7])
                print(name, K, f"{time.time()-t0:.0f}s", flush=True)
