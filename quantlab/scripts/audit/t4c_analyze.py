"""Analysis of the K-grid / diagnostic-alternatives study -> docs/audit/t4c_table.csv, t4c_summary.json"""
import os, sys, glob, json
import numpy as np, pandas as pd
from scipy.stats import norm, skew
sys.path.insert(0, os.path.dirname(__file__))
from t3_analyze import cp

RAW = "docs/audit/raw/t4c"
LV = [0.10, 0.05, 0.01, 0.0025, 0.00125]
rows = []
for f in sorted(glob.glob(f"{RAW}/*.npz")):
    name = os.path.basename(f)[:-4]; scen, K = name.rsplit("_K", 1)
    z = np.load(f); ok = np.isfinite(z["obs"]); obs = z["obs"][ok]; S = len(obs)
    sd = obs.std(ddof=1)
    P = {"boot": z["p_boot"][ok], "t": z["p_t"][ok], "nw": z["p_nw"][ok], "cbb3": z["p_cbb3"][ok], "oracle": norm.sf(obs / sd)}
    r = {"scenario": scen, "K": int(K), "reps": S, "mean_clusters": float(z["n_clusters"][ok].mean()), "mean_trades": float(z["n_trades"][ok].mean()),
         "design_effect_true_var/boot_var": float(obs.var(ddof=1) / z["boot_var"][ok].mean()), "skew_obs": float(skew(obs))}
    for k, p in P.items():
        for a in LV:
            n = int((p <= a).sum()); lo, hi = cp(n, S)
            r[f"{k}@{a}"] = n / S / a; r[f"{k}_lo@{a}"] = lo / a; r[f"{k}_hi@{a}"] = hi / a
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv("docs/audit/t4c_table.csv", index=False)
json.dump(T.to_dict(orient="records"), open("docs/audit/t4c_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
for a in (0.05, 0.00125):
    print(f"--- ratio (actual/nominal) at {a}")
    print(T.pivot(index=["scenario"], columns="K", values=f"boot@{a}").round(2).to_string())
print("--- design effect (true var / bootstrap var)")
print(T.pivot(index="scenario", columns="K", values="design_effect_true_var/boot_var").round(2).to_string())
print("--- at K=24, ratio@0.00125 per method")
print(T[T.K == 24].set_index("scenario")[[f"{k}@0.00125" for k in ("boot", "t", "nw", "cbb3", "oracle")]].round(2).to_string())
print("--- at K=24, ratio@0.01 per method")
print(T[T.K == 24].set_index("scenario")[[f"{k}@0.01" for k in ("boot", "t", "nw", "cbb3", "oracle")]].round(2).to_string())
