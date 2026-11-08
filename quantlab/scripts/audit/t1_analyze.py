"""Task 1 analysis: per-sampler-variant calibration + diagnostic metrics. usage: python scripts/audit/t1_analyze.py <csv> [--json out]"""
import sys, json, os
import numpy as np, pandas as pd
from scipy.stats import beta


def cp(k, n, conf=0.95):
    a = (1 - conf) / 2
    return (0.0 if k == 0 else beta.ppf(a, k, n - k + 1), 1.0 if k == n else beta.ppf(1 - a, k + 1, n - k))


def analyze(path):
    d = pd.read_csv(path)
    xp = path.replace("/t1_", "/t1_extra_")
    if os.path.exists(xp):
        x = pd.read_csv(xp)
        d = pd.concat([d, x[x.config != "G_exact"]], ignore_index=True)
    g = d[d.config == "G_exact"].set_index("k")
    rows = []
    for name, x in d.groupby("config", sort=False):
        x = x.set_index("k")
        n = len(x)
        z = (x.obs - x.mean_c) / x.sd_c
        r = {"config": name, "n_studies": n, "success": x.success.mean()}
        for a in (0.10, 0.05, 0.01):
            k = int((x.p <= a).sum()); lo, hi = cp(k, n)
            r[f"rate{a}"] = k / n; r[f"ratio{a}"] = k / n / a; r[f"ci_lo{a}"] = lo / a; r[f"ci_hi{a}"] = hi / a
        r["mean_z"] = z.mean(); r["var_z"] = z.var(ddof=1)
        zg = ((g.obs - g.mean_c) / g.sd_c).loc[x.index]
        rng = np.random.default_rng(0); bs = []
        for _ in range(300):
            ii = rng.integers(0, n, n); bs.append(z.values[ii].var(ddof=1) - zg.values[ii].var(ddof=1))
        r["dvar_z_vs_G"] = float(z.var(ddof=1) - zg.var(ddof=1)); r["dvar_se"] = float(np.std(bs))
        gg = g.loc[x.index]
        r["sd_ratio_vs_G"] = float((x.sd_c / gg.sd_c).median()); r["mean_shift_sdG"] = float(((x.mean_c - gg.mean_c) / gg.sd_c).mean())
        if name != "G_exact":
            zK = (x.K_obs - x.K_mean) / x.K_sd
            r["K_obs/K_ctrl"] = float(x.K_obs.mean() / x.K_mean.mean()); r["zK"] = float(zK.mean())
            r["cp7_obs"] = float(x.cp7_obs.mean()); r["cp7_ctrl"] = float(x.cp7_mean.mean())
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t = analyze(sys.argv[1])
    pd.set_option("display.width", 250)
    if len(sys.argv) > 2:
        t.to_csv(sys.argv[2], index=False)
    print(t[["config", "n_studies", "success", "ratio0.1", "ratio0.05", "ratio0.01", "ci_lo0.05", "ci_hi0.05", "mean_z", "var_z", "dvar_z_vs_G", "dvar_se", "sd_ratio_vs_G", "mean_shift_sdG", "K_obs/K_ctrl", "cp7_obs", "cp7_ctrl"]].round(3).to_string())
