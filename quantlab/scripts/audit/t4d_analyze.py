"""Analysis of the 82-family simulations -> docs/audit/t4d_family_table.csv, t4d_summary.json"""
import os, sys, glob, json, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from t3_analyze import cp
M = 82
rows = []
for f in sorted(glob.glob("docs/audit/raw/t4d/fam_*.npy")):
    a = np.load(f); F = len(a); name = os.path.basename(f)[4:-4]
    scen = re.match(r"(.*)_rho", name).group(1); rho = float(re.search(r"rho([\d.]+)", name).group(1)); nt = int(re.search(r"true(\d+)", name).group(1))
    staged = name.endswith("staged")
    k = int(a[:, 0].sum()); lo, hi = cp(k, F)
    n_null_tested = a[:, 6].mean(); n_true_tested = a[:, 7].mean()
    r = {"config": name, "scenario": scen, "rho_between_strategies": rho, "n_true_effects": nt, "selection": "staged DEV-screen->VALID(fresh data)" if staged else "all 82 tested",
         "families": F, "FWER_holm_0.10": k / F, "FWER_ci_lo": lo, "FWER_ci_hi": hi,
         "mean_false_rejections_after_holm": a[:, 1].mean(),
         "mean_false_rejections_raw_p<=0.10/82 (before Holm)": a[:, 3].mean(),
         "per_test_false_rate_raw_p<=0.10/82_vs_nominal": a[:, 3].sum() / (F * n_null_tested) / (0.10 / M) if n_null_tested else np.nan,
         "per_test_false_rate_raw_p<=0.10_vs_nominal": a[:, 2].sum() / (F * n_null_tested) / 0.10 if n_null_tested else np.nan,
         "mean_null_tested": n_null_tested, "power_holm_true_rejected": (a[:, 4].sum() / (F * nt)) if nt else np.nan}
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv("docs/audit/t4d_family_table.csv", index=False); json.dump({"table": T.to_dict(orient="records"), "holm_independent_check": json.load(open("docs/audit/raw/t4d/holm_independent_check.json")) if os.path.exists("docs/audit/raw/t4d/holm_independent_check.json") else None}, open("docs/audit/t4d_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 40)
print(T.drop(columns=["config", "families"]).round(3).to_string())
