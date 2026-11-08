"""Task 4 analysis -> docs/audit/t4_bootstrap_table.csv, t4_summary.json (scenario calibration, resolution table, resamples-needed, Holm FWER)."""
import os, sys, json, glob
import numpy as np, pandas as pd
from scipy.stats import beta, binom
sys.path.insert(0, os.path.dirname(__file__))
from t3_analyze import cp, mdr80

RAW = "docs/audit/raw/t4"
LV = [0.10, 0.05, 0.01, 0.005, 0.0025, 0.00125, 0.001]
N = 5000


def scen_table():
    cfg = json.load(open(f"{RAW}/t4_config.json"))
    rows = []
    for sc in cfg["scenarios"]:
        f = f"{RAW}/{sc['name']}.npz"
        if not os.path.exists(f):
            continue
        z = np.load(f); p = (1 + z["count"].astype(float)) / (N + 1); S = len(p)
        r = {"scenario": sc["name"], "reps": S, "mean_trades": float(z["n_trades"].mean()), "mean_clusters": float(z["n_clusters"].mean()), "mean_p": float(p.mean()),
             "share_p_at_min(1/5001)": float((z["count"] == 0).mean())}
        for a in LV:
            k = int((p <= a).sum()); lo, hi = cp(k, S)
            r[f"ratio@{a}"] = k / S / a; r[f"lo@{a}"] = lo / a; r[f"hi@{a}"] = hi / a; r[f"k@{a}"] = k
        r["mdr80@0.00125"] = mdr80(S, 0.00125)
        rows.append(r)
    return pd.DataFrame(rows)


def resolution_table():
    """P(reject at 0.00125) when the TRUE bootstrap-limit p equals p*, for n resamples (p-hat = (1+X)/(n+1), X~Bin(n,p*)): shows MC noise of the decision."""
    out = []
    for n in (1000, 5000, 20000, 100000, 1000000):
        for ps in (0.0005, 0.00075, 0.001, 0.00125, 0.0015, 0.002, 0.003):
            cmax = np.floor(0.00125 * (n + 1) - 1)                    # reject iff X <= cmax
            out.append({"n_resamples": n, "true_p": ps, "P_reject_at_0.00125": float(binom.cdf(cmax, n, ps)) if cmax >= 0 else 0.0,
                        "rel_sd_of_phat": float(np.sqrt((1 - ps) / (ps * n))), "min_possible_p": 1 / (n + 1)})
    return pd.DataFrame(out)


def part_a():
    res = {}
    for f in glob.glob(f"{RAW}/t4a_resamples_*.npy"):
        name = os.path.basename(f)[len("t4a_resamples_"):-4]
        c = np.load(f); S = len(c); r = {"reps": S}
        for q, n in enumerate((1000, 5000, 20000, 100000, "5000_fixed_seed")):
            nn = 5000 if n == "5000_fixed_seed" else n
            p = (1 + c[:, q]) / (nn + 1)
            r[str(n)] = {f"ratio@{a}": float((p <= a).mean() / a) for a in (0.01, 0.0025, 0.00125)} | {f"k@{a}": int((p <= a).sum()) for a in (0.01, 0.0025, 0.00125)}
        p5, p100 = (1 + c[:, 1]) / 5001, (1 + c[:, 3]) / 100001
        d = (p5 <= 0.00125); e = (p100 <= 0.00125)
        r["decision_5000_vs_100000@0.00125"] = {"only5000": int((d & ~e).sum()), "only100000": int((~d & e).sum()), "both": int((d & e).sum())}
        res[name] = r
    return res


def holm_part():
    res = {}
    for f in sorted(glob.glob(f"{RAW}/t4b_holm_*.npy")):
        a = np.load(f); S = len(a)
        k = int(a[:, 2].sum()); lo, hi = cp(k, S)
        res[os.path.basename(f)[9:-4]] = {"families": S, "FWER@0.10(Holm,m=82)": k / S, "ci": [lo, hi], "P(min p<=0.10/82)": float((a[:, 0] <= 0.10 / 82).mean()),
                                         "mean_n_p<=0.10/82": float(a[:, 3].mean())}
    return res


if __name__ == "__main__":
    T = scen_table(); R = resolution_table()
    T.to_csv("docs/audit/t4_bootstrap_table.csv", index=False); R.to_csv("docs/audit/t4_resolution_table.csv", index=False)
    out = {"scenarios": T.to_dict(orient="records"), "resolution": R.to_dict(orient="records"), "resamples": part_a(), "holm_fwer": holm_part()}
    json.dump(out, open("docs/audit/t4_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    if len(T):
        print(T[["scenario", "reps", "mean_trades", "mean_clusters", "ratio@0.1", "ratio@0.05", "ratio@0.01", "ratio@0.0025", "ratio@0.00125", "lo@0.00125", "hi@0.00125", "share_p_at_min(1/5001)"]].round(3).to_string())
    print(R[R.n_resamples.isin([5000, 100000])].round(4).to_string())
    print(json.dumps(out["holm_fwer"], indent=1, default=float))
