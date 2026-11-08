"""Task 5 analysis -> docs/audit/t5_trade_table.csv, t5_summary.json"""
import os, sys, glob, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from t3_analyze import cp, mdr80, mcnemar_exact

LV = [0.10, 0.05, 0.01, 0.005]
rows = []
for f in sorted(glob.glob("docs/audit/raw/t5_*.csv")):
    d = pd.read_csv(f); name = os.path.basename(f)[3:-4]
    d = d[d.n_real.fillna(0) >= 2]
    n = len(d)
    z = (d.obs - d.ctrl_mean) / d.ctrl_sd
    r = {"setting": name, "n_studies": n, "mean_real_trades": d.n_real.mean(), "mean_exec_controls_before_subsample": d.n_exec_mean.mean(),
         "share_reps_with_too_few_controls": d.short_frac.mean(), "sd_ratio_ctrl/ref(median)": float((d.ctrl_sd / d.ref_sd).median()),
         "mean_z": z.mean(), "var_z": z.var(ddof=1), "held_ratio_ctrl/real": float((d.ctrl_held / d.real_held).mean()),
         "mean_ctrl_minus_all_mean": float((d.ctrl_mean - d.ctrl_all_mean).mean())}
    for a in LV:
        for col in ("p_prod", "p_nosub", "p_ref"):
            k = int((d[col] <= a).sum()); lo, hi = cp(k, n)
            r[f"{col}@{a}"] = k / n / a; r[f"{col}_lo@{a}"] = lo / a; r[f"{col}_hi@{a}"] = hi / a
        b = int(((d.p_prod <= a) & ~(d.p_ref <= a)).sum()); c = int((~(d.p_prod <= a) & (d.p_ref <= a)).sum())
        r[f"mcnemar_prod_vs_ref@{a}"] = mcnemar_exact(b, c)
    r["mdr80@0.10"] = mdr80(n, 0.10); r["min_possible_p"] = 1 / 501
    rows.append(r)
T = pd.DataFrame(rows)
if len(T):
    T.to_csv("docs/audit/t5_trade_table.csv", index=False); json.dump(T.to_dict(orient="records"), open("docs/audit/t5_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(T[["setting", "n_studies", "mean_real_trades", "mean_exec_controls_before_subsample", "share_reps_with_too_few_controls", "sd_ratio_ctrl/ref(median)", "var_z", "p_prod@0.1", "p_prod_lo@0.1", "p_prod_hi@0.1", "p_prod@0.05", "p_ref@0.1", "p_nosub@0.1", "mcnemar_prod_vs_ref@0.1"]].round(3).to_string())
