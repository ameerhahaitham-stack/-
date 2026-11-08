"""Supplementary audit T9: how much extra protection do the OTHER VALID gates give once the monthly-bootstrap gate has passed? Synthetic null, K=24 months, 5 trades/month.
Gates reproduced from protocol criteria.valid (those computable from a trade-R series): expectancy>=0.10R, PF>=1.2, expectancy ex top-5 trades >0, positive-year share>=0.5
(two calendar years of 12 months), total R / max drawdown (R) >= 1 and DD<=20R. Costs/neighbour/stress/control gates are NOT simulated here.
Reports P(bootstrap p<=0.00125), P(gate | bootstrap pass), P(all) with exact CIs."""
import os, sys, json
import numpy as np, pandas as pd
from scipy.stats import beta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootalt import SCEN, gen_month_sums, all_p

SEED0 = 20261123
K, NPM, REPS = 24, 5, 60000
rows = []
for si, sc in enumerate(("N2_iid_rr2", "T2_tradeAR0.3", "M4_monthEff0.25_AR0.8", "M3_monthEff0.5_AR0.8", "S1_streak0.9", "T3_tradeAR0.7")):
    acc = {k: 0 for k in ("boot", "exp", "pf", "top5", "year", "dd", "all_other", "all")}
    cond = {k: 0 for k in ("exp", "pf", "top5", "year", "dd", "all_other")}
    for ci in range(REPS // 5000):
        S, r = gen_month_sums(sc, K, NPM, 5000, np.random.default_rng([SEED0, si, ci]), trades=True)
        pb = all_p(S, NPM)["boot"] <= 0.00125
        exp = r.mean(1) >= 0.10
        gains = np.where(r > 0, r, 0).sum(1); losses = -np.where(r < 0, r, 0).sum(1)
        pf = gains >= 1.2 * np.maximum(losses, 1e-9)
        top5 = (r.sum(1) - np.sort(r, 1)[:, -5:].sum(1)) > 0
        half = K * NPM // 2
        y1 = r[:, :half].mean(1) > 0; y2 = r[:, half:].mean(1) > 0
        year = (y1.astype(int) + y2.astype(int)) / 2 >= 0.5
        cum = np.cumsum(r, 1); dd = (np.maximum.accumulate(np.maximum(cum, 0), 1) - cum).max(1)
        ddok = (dd <= 20) & ((r.sum(1) / np.maximum(dd, 1e-9)) >= 1.0)
        other = exp & pf & top5 & year & ddok
        for k, v in (("boot", pb), ("exp", exp), ("pf", pf), ("top5", top5), ("year", year), ("dd", ddok), ("all_other", other), ("all", pb & other)):
            acc[k] += int(v.sum())
        for k, v in (("exp", exp), ("pf", pf), ("top5", top5), ("year", year), ("dd", ddok), ("all_other", other)):
            cond[k] += int((pb & v).sum())
    n = REPS; nb = acc["boot"]
    def ci(x, m):
        return (beta.ppf(.025, x, m - x + 1) if x else 0.0, beta.ppf(.975, x + 1, m - x) if x < m else 1.0)
    rows.append(dict(scenario=sc, reps=n, p_boot_gate=nb / n, p_boot_ci_lo=ci(nb, n)[0], p_boot_ci_hi=ci(nb, n)[1], p_other_gates_alone=acc["all_other"] / n,
                     p_all_gates=acc["all"] / n, p_all_ci_lo=ci(acc["all"], n)[0], p_all_ci_hi=ci(acc["all"], n)[1],
                     **{f"cond_{k}": (cond[k] / nb if nb else np.nan) for k in cond}))
df = pd.DataFrame(rows); df.to_csv("docs/audit/t9_gates.csv", index=False)
print(df.round(5).to_string())
