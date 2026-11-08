"""Task 4 runner (null calibration of the monthly cluster bootstrap). usage: python scripts/audit/t4_bootstrap.py [--reps 60000] [--only name]
Raw output per scenario: docs/audit/raw/t4/<name>.npz with uint16 `count` (= #resamples with centred-null mean >= observed mean; p=(1+count)/5001),
n_trades, n_clusters. Deterministic seeds: default_rng([SEED0, scenario_index, chunk])."""
import argparse, os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootcal import Scenario, simulate_trades, month_sums, prod_idx
from multiprocessing import Pool

SEED0 = 20261107
S = Scenario
SCENARIOS = [
    # --- A: independent returns (distribution shape) ---
    S("A1_iid_normal"), S("A2_iid_rr2", r_dist="rr2"), S("A3_iid_rr3", r_dist="rr3"), S("A4_iid_t3", r_dist="t3"),
    # --- B: autocorrelation between consecutive trades (medium 0.3 / high 0.7) ---
    S("B1_ar0.3_rr2", r_dist="rr2", phi_trade=0.3), S("B2_ar0.7_rr2", r_dist="rr2", phi_trade=0.7), S("B3_ar0.7_normal", phi_trade=0.7),
    # --- C: serial dependence between months (cluster effect 0.5 sd with AR 0.5 / 0.8 across months) ---
    S("C1_month_eff0.5", r_dist="rr2", month_effect=0.5), S("C2_month_eff0.5_ar0.5", r_dist="rr2", month_effect=0.5, phi_month=0.5),
    S("C3_month_eff0.5_ar0.8", r_dist="rr2", month_effect=0.5, phi_month=0.8), S("C4_month_eff1.0_ar0.8", r_dist="rr2", month_effect=1.0, phi_month=0.8),
    # --- D: volatility differences between months ---
    S("D1_vol0.5_rr2", r_dist="rr2", vol_sd=0.5), S("D2_vol1.0_rr2", r_dist="rr2", vol_sd=1.0), S("D3_vol1.0_ar0.7_ma0.8", r_dist="rr2", vol_sd=1.0, phi_trade=0.7, month_effect=0.5, phi_month=0.8),
    # --- E: clustering of profits and losses in time (regimes / streaks) ---
    S("E1_streak0.9_rr2", r_dist="rr2", streaks=0.9), S("E2_streak0.97_rr2", r_dist="rr2", streaks=0.97),
    # --- F: sample size (trades per active month) and window length ---
    S("F1_n1_perm_rr2", r_dist="rr2", n_per_month=1), S("F2_n2_perm_rr2", r_dist="rr2", n_per_month=2), S("F3_n10_perm_rr2", r_dist="rr2", n_per_month=10),
    S("F4_n20_perm_rr2", r_dist="rr2", n_per_month=20), S("F5_K12_rr2", r_dist="rr2", K=12), S("F6_K60_rr2", r_dist="rr2", K=60), S("F7_K60_n2_rr2", r_dist="rr2", K=60, n_per_month=2),
    # --- G: uneven trade counts across months (sparse / dense) ---
    S("G1_poisson_n3_rr2", r_dist="rr2", month_dist="poisson", n_per_month=3), S("G2_negbin_n5_rr2", r_dist="rr2", month_dist="negbin", n_per_month=5),
    S("G3_sparse_n3_rr2", r_dist="rr2", month_dist="sparse", n_per_month=3), S("G4_sparse_n8_rr2", r_dist="rr2", month_dist="sparse", n_per_month=8),
    S("G5_negbin_n2_K12_rr2", r_dist="rr2", month_dist="negbin", n_per_month=2, K=12),
]


def _chunk(args):
    si, ci, nrep = args
    sc = SCENARIOS[si]
    rng = np.random.default_rng([SEED0, si, ci])
    cnt = np.zeros(nrep, np.uint16); nt = np.zeros(nrep, np.uint16); kc = np.zeros(nrep, np.uint8)
    for j in range(nrep):
        r, mid = simulate_trades(sc, rng)
        s, c = month_sums(r, mid)
        K = len(s)
        nt[j], kc[j] = len(r), K
        if K < 2:
            cnt[j] = 5000
            continue
        idx = prod_idx(K)
        means = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
        obs = s.sum() / c.sum()
        cnt[j] = int(((means - obs) >= obs).sum())
    return cnt, nt, kc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=60000); ap.add_argument("--only", default=None)
    ap.add_argument("--procs", type=int, default=2); ap.add_argument("--out", default="docs/audit/raw/t4")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    json.dump({"seed0": SEED0, "reps": a.reps, "scenarios": [s.__dict__ for s in SCENARIOS], "bootstrap": {"n": 5000, "seed": 12345, "kind": "month"}},
              open(os.path.join(a.out, "t4_config.json"), "w"), indent=1)
    chunk = 2500
    with Pool(a.procs) as pool:
        for si, sc in enumerate(SCENARIOS):
            if a.only and a.only not in sc.name:
                continue
            f = os.path.join(a.out, sc.name + ".npz")
            if os.path.exists(f):
                continue
            t0 = time.time()
            jobs = [(si, ci, min(chunk, a.reps - ci * chunk)) for ci in range((a.reps + chunk - 1) // chunk)]
            res = pool.map(_chunk, jobs)
            np.savez_compressed(f, count=np.concatenate([r[0] for r in res]), n_trades=np.concatenate([r[1] for r in res]), n_clusters=np.concatenate([r[2] for r in res]))
            print(f"{sc.name}: {a.reps} reps in {time.time()-t0:.0f}s", flush=True)
