"""Supplementary audit T7: empty months / gap compression / unequal counts. Writes docs/audit/raw/t7/*.npz (p arrays) and docs/audit/t7_gaps_size.csv."""
import argparse, os, sys, json, time
import numpy as np, pandas as pd
from scipy.stats import beta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.gaps import GSC, gap_pvals, gen, LAM

SEED0 = 20261121
LEV = [0.10, 0.05, 0.01, 0.00125]
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=60000); ap.add_argument("--Kc", type=int, nargs="+", default=[24, 60])
    ap.add_argument("--out", default="docs/audit/raw/t7"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    json.dump({"seed0": SEED0, "reps": a.reps, "Kc": a.Kc, "lam": LAM, "scenarios": GSC, "nb": 5000}, open(f"{a.out}/t7_config.json", "w"), indent=1)
    rows = []
    for Kc in a.Kc:
        for si, sc in enumerate(GSC):
            f = f"{a.out}/{sc}_Kc{Kc}.npz"
            if not os.path.exists(f):
                t0 = time.time(); P = {}
                for ci, st in enumerate(range(0, a.reps, 4000)):
                    s, c = gen(sc, Kc, min(4000, a.reps - st), np.random.default_rng([SEED0, si, Kc, ci]))
                    for k, v in gap_pvals(s, c).items():
                        P.setdefault(k, []).append(v)
                np.savez_compressed(f, **{k: np.concatenate(v).astype(np.float32) for k, v in P.items()}); print(sc, Kc, f"{time.time()-t0:.0f}s", flush=True)
            d = np.load(f); n = len(d["prod"])
            for m in ("prod", "cal", "cbb_act", "cbb_cal", "t_act", "kv_cal", "im_cal"):
                for lv in LEV:
                    x = int((d[m] <= lv).sum()); lo = beta.ppf(.025, x, n - x + 1) if x else 0.0; hi = beta.ppf(.975, x + 1, n - x)
                    rows.append(dict(Kc=Kc, scenario=sc, method=m, level=lv, reps=n, rejections=x, rate=x / n, ratio=x / n / lv, ci_lo=lo / lv, ci_hi=hi / lv,
                                     mean_active=float(d["_n_active"].mean()), mean_trades=float(d["_n_trades"].mean())))
    pd.DataFrame(rows).to_csv("docs/audit/t7_gaps_size.csv", index=False)
