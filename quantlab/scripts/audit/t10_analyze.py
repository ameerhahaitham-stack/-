"""Analyse T10 (drift-regime null, always-long random-timing signals): bootstrap gate x matched-control gate, exact CIs."""
import os, sys, glob, json
import numpy as np, pandas as pd
from scipy.stats import beta

def cp(x, n):
    return (beta.ppf(.025, x, n - x + 1) if x else 0.0, beta.ppf(.975, x + 1, n - x) if x < n else 1.0)

rows = []
for name in ("D0", "D1", "D2"):
    f = f"docs/audit/raw/t10_{name}.csv"
    if not os.path.exists(f):
        continue
    d = pd.read_csv(f); d = d[d.n_real > 0]; n = len(d)
    r = dict(setting=name, studies=n, mean_R=float(d.obs.mean()), sd_of_mean_R=float(d.obs.std()), mean_trades=float(d.n_real.mean()), mean_clusters=float(d.n_clusters.mean()))
    for L in (0.10, 0.05, 0.01, 0.00125):
        x = int((d.p_boot <= L).sum()); lo, hi = cp(x, n)
        r[f"boot<= {L}"] = x / n; r[f"boot<= {L} ratio"] = x / n / L; r[f"boot<= {L} ci"] = f"[{lo/L:.2f},{hi/L:.2f}]"
    for L in (0.10, 0.05, 0.01):
        x = int((d.p_ctrl <= L).sum()); lo, hi = cp(x, n)
        r[f"ctrl<= {L}"] = x / n; r[f"ctrl<= {L} ratio"] = x / n / L; r[f"ctrl<= {L} ci"] = f"[{lo/L:.2f},{hi/L:.2f}]"
    for L in (0.10, 0.05, 0.01, 0.00125):
        b = d.p_boot <= L; x = int((b & (d.p_ctrl <= 0.10)).sum())
        r[f"joint boot<= {L} & ctrl<=0.10"] = x / n; r[f"joint {L} count"] = x
        r[f"P(ctrl<=0.10 | boot<= {L})"] = (x / b.sum()) if b.sum() else np.nan
    r["corr(p_boot,p_ctrl)"] = float(d[["p_boot", "p_ctrl"]].corr(method="spearman").iloc[0, 1])
    rows.append(r)
R = pd.DataFrame(rows); R.to_csv("docs/audit/t10_drift_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
print(R.T.to_string())
