"""Analyse the raw tail-calibration CSVs -> docs/control_tail_calibration.json (+ printed tables).
python scripts/control_tail_report.py docs/calibration_raw/tail_phi0.8.csv [docs/calibration_raw/tail_phi0.95.csv ...]"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

ALPHAS = (0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.10)
BINS = (0.0, 0.001, 0.0025, 0.005, 0.01)


def cp(k, n, conf=0.95):                                    # Clopper-Pearson (exact) interval
    lo = 0.0 if k == 0 else stats.beta.ppf((1 - conf) / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - (1 - conf) / 2, k + 1, n - k)
    return float(lo), float(hi)


def min_detectable_ratio(n, alpha, power=0.8, size=0.05):
    """Smallest true/nominal ratio r such that a one-sided exact binomial test at `size` detects rate r*alpha with `power`."""
    crit = stats.binom.ppf(1 - size, n, alpha)               # reject if count > crit
    for r in np.arange(1.0, 20.0, 0.05):
        if stats.binom.sf(crit, n, min(r * alpha, 1.0)) >= power:
            return float(round(r, 2))
    return None


def table(p: np.ndarray, label: str) -> list[dict]:
    n, rows = len(p), []
    for a in ALPHAS:
        k = int((p <= a).sum())
        lo, hi = cp(k, n)
        rows.append({"series": label, "alpha": a, "n": n, "expected_count": n * a, "count": k, "rate": k / n, "ci95": [lo, hi],
                     "ratio": (k / n) / a, "ratio_ci95": [lo / a, hi / a], "p_excess_onesided": float(stats.binom.sf(k - 1, n, a)),
                     "min_detectable_ratio_80pct_power": min_detectable_ratio(n, a),
                     "status": ("EXCESS_DETECTED" if lo > a else ("NO_EVIDENCE_OF_EXCESS_(upper<=2x)" if hi <= 2 * a else "INCONCLUSIVE_(upper>2x)"))})
    return rows


def bins(p, label):
    n = len(p); out = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        k = int(((p > lo) & (p <= hi)).sum()) if lo > 0 else int((p <= hi).sum())
        out.append({"series": label, "bin": [lo, hi], "observed": k, "expected": n * (hi - lo)})
    obs = np.array([b["observed"] for b in out]); exp = np.array([b["expected"] for b in out])
    rest_o, rest_e = n - obs.sum(), n - exp.sum()
    chi = float((((obs - exp) ** 2) / exp).sum() + ((rest_o - rest_e) ** 2) / rest_e)
    return out, {"chi2": chi, "df": len(obs), "p": float(stats.chi2.sf(chi, len(obs)))}


def main(files):
    res = {}
    for f in files:
        d = pd.read_csv(f)
        name = Path(f).stem
        sha = hashlib.sha256(Path(f).read_bytes()).hexdigest()
        r = {"file": str(f), "sha256": sha, "n_studies": len(d), "mean_events": float(d["n_events"].mean()),
             "min_coverage": float(d["coverage"].min()), "n_refined": int(d["refined"].sum()), "n_unique_k": int(d["k"].nunique())}
        for col in ("p_prod", "p_ref"):
            r[f"{col}_table"] = table(d[col].to_numpy(), col)
            b, chi = bins(d[col].to_numpy(), col)
            r[f"{col}_bins"], r[f"{col}_bins_chi2"] = b, chi
            r[f"{col}_mean"] = float(d[col].mean())
        r["spearman_prod_vs_ref"] = float(stats.spearmanr(d["p_prod"], d["p_ref"])[0])
        r["spearman_log"] = float(stats.spearmanr(np.log(d["p_prod"]), np.log(d["p_ref"]))[0])
        r["median_log_ratio_prod_over_ref_when_ref_le_0.005"] = float(np.median(np.log(d.loc[d["p_ref"] <= 0.005, "p_prod"] / d.loc[d["p_ref"] <= 0.005, "p_ref"]))) if (d["p_ref"] <= 0.005).any() else None
        pair = {}
        for a in (0.001, 0.005, 0.05):
            both = int(((d.p_prod <= a) & (d.p_ref <= a)).sum()); only_prod = int(((d.p_prod <= a) & (d.p_ref > a)).sum()); only_ref = int(((d.p_prod > a) & (d.p_ref <= a)).sum())
            disc = only_prod + only_ref
            pair[str(a)] = {"both": both, "only_prod": only_prod, "only_ref": only_ref,
                            "mcnemar_exact_two_sided_p": float(stats.binomtest(only_prod, disc, 0.5).pvalue) if disc else 1.0}
        r["paired_decisions"] = pair
        res[name] = r
    out = Path(__file__).resolve().parents[1] / "docs" / "control_tail_calibration.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for name, r in res.items():
        print(f"\n== {name}: studies {r['n_studies']}  mean events {r['mean_events']:.1f}  min coverage {r['min_coverage']}  refined {r['n_refined']}  sha256 {r['sha256'][:16]}")
        for col in ("p_prod", "p_ref"):
            print(f"  [{col}] mean p {r[col+'_mean']:.4f}  bins chi2 p={r[col+'_bins_chi2']['p']:.3f}")
            for t in r[f"{col}_table"]:
                print(f"    a={t['alpha']:<7} exp {t['expected_count']:7.1f} obs {t['count']:5d} rate {t['rate']:.5f} ratio {t['ratio']:.2f} CI95x [{t['ratio_ci95'][0]:.2f},{t['ratio_ci95'][1]:.2f}] "
                      f"excess-p {t['p_excess_onesided']:.3f} MDR80 {t['min_detectable_ratio_80pct_power']}  {t['status']}")
        print("  spearman", round(r["spearman_prod_vs_ref"], 3), "paired", r["paired_decisions"])
    print("\nsaved", out)


if __name__ == "__main__":
    main(sys.argv[1:])
