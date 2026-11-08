"""Analyse docs/audit/raw/t6: size (exact Clopper-Pearson CIs), power, minimum detectable effect and long-run-variance reliability."""
import os, sys, json, glob
import numpy as np, pandas as pd
from scipy.stats import beta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit.bootalt import SCEN

R = "docs/audit/raw/t6"
METH = ["boot", "t", "nw1", "nw3", "kv", "ar1", "imq4", "imb6", "imb3", "cbb3", "oracle"]
LEV = [0.10, 0.05, 0.01, 0.00125]
MUS = [0.1, 0.2, 0.3, 0.5]


def cp(x, n, a=0.05):
    lo = 0.0 if x == 0 else beta.ppf(a / 2, x, n - x + 1)
    hi = 1.0 if x == n else beta.ppf(1 - a / 2, x + 1, n - x)
    return lo, hi


rows, prow, lrow = [], [], []
for K in (24, 60):
    for sc in SCEN:
        f0 = f"{R}/{sc}_K{K}_mu0.0.npz"
        if not os.path.exists(f0):
            continue
        d = np.load(f0)
        n = len(d["boot"])
        for m in METH:
            for lv in LEV:
                x = int((d[m] <= lv).sum())
                lo, hi = cp(x, n)
                rows.append(dict(K=K, scenario=sc, tier=SCEN[sc]["tier"], method=m, level=lv, reps=n, rejections=x, rate=x / n, ratio=x / n / lv, ci_lo=lo / lv, ci_hi=hi / lv))
        tv = float(np.var(d["_m"]))
        for e, key in (("boot", "_v_boot"), ("t", "_v_t"), ("nw1", "_v_nw1"), ("nw3", "_v_nw3"), ("kv", "_v_kv"), ("ar1", "_v_ar1"), ("imb6", "_v_imb6")):
            v = d[key]
            lrow.append(dict(K=K, scenario=sc, tier=SCEN[sc]["tier"], estimator=e, mean_ratio=float(v.mean() / tv), median_ratio=float(np.median(v) / tv),
                             cv=float(v.std() / v.mean()), p_under70=float((v < 0.7 * tv).mean()), p_under50=float((v < 0.5 * tv).mean())))
        for mu in MUS:
            f = f"{R}/{sc}_K{K}_mu{mu}.npz"
            if not os.path.exists(f):
                continue
            dd = np.load(f); nn = len(dd["boot"])
            for m in METH:
                for lv in (0.05, 0.00125):
                    x = int((dd[m] <= lv).sum()); lo, hi = cp(x, nn)
                    prow.append(dict(K=K, scenario=sc, method=m, mu=mu, level=lv, reps=nn, power=x / nn, ci_lo=lo, ci_hi=hi))
S = pd.DataFrame(rows); P = pd.DataFrame(prow); L = pd.DataFrame(lrow)
S.to_csv("docs/audit/t6_size.csv", index=False); P.to_csv("docs/audit/t6_power.csv", index=False); L.to_csv("docs/audit/t6_lrv.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)
for lv in (0.00125, 0.05):
    print(f"\n=== size ratio actual/nominal at {lv}")
    t = S[S.level == lv].pivot_table(index=["K", "scenario"], columns="method", values="ratio")[METH]
    print(t.round(2).to_string())
print("\n=== K=24 vs K=60 at 0.00125 (ratio, CI) for production bootstrap")
b = S[(S.method == "boot") & (S.level == 0.00125)].pivot_table(index="scenario", columns="K", values=["ratio", "ci_lo", "ci_hi"])
print(b.round(2).to_string())
print("\n=== LRV reliability: mean(v_hat)/true var (K, scenario)")
print(L.pivot_table(index=["K", "scenario"], columns="estimator", values="mean_ratio").round(2).to_string())
print("\n=== P(v_hat < 0.7 true)")
print(L.pivot_table(index=["K", "scenario"], columns="estimator", values="p_under70").round(2).to_string())
print("\n=== power at 0.00125 (scenario N2, V1, M4, T2, M3)")
for sc in ("N2_iid_rr2", "T2_tradeAR0.3", "M4_monthEff0.25_AR0.8", "M3_monthEff0.5_AR0.8"):
    q = P[(P.scenario == sc) & (P.level == 0.00125)].pivot_table(index=["K", "mu"], columns="method", values="power")
    print(sc); print(q[[c for c in ["boot", "t", "nw3", "kv", "ar1", "imq4", "imb6", "cbb3", "oracle"] if c in q]].round(3).to_string())
