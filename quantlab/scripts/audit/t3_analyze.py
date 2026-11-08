"""Tasks 2-3 analysis: tail calibration table (counts, rates, ratios, exact CIs, MDR80, paired McNemar) for every (mode, phi, p-type).
usage: python scripts/audit/t3_analyze.py  -> docs/audit/t3_tail_table.csv, docs/audit/t3_summary.json"""
import os, sys, json, glob
import numpy as np, pandas as pd
from scipy.stats import beta, binom

RAW = "docs/audit/raw"
LEVELS = [0.10, 0.05, 0.01, 0.005, 0.0025, 0.001]
PRE_CUT = 0.02


def cp(k, n, conf=0.95):
    a = (1 - conf) / 2
    return (0.0 if k == 0 else beta.ppf(a, k, n - k + 1), 1.0 if k == n else beta.ppf(1 - a, k + 1, n - k))


def mdr80(n, a, alpha=0.05, power=0.8):
    """smallest ratio r such that a one-sided exact binomial test of H0: rate<=a (size<=alpha) has power >= `power` against rate=r*a."""
    c = int(binom.isf(alpha, n, a)) + 1                      # smallest c with P(X>=c) <= alpha
    while binom.sf(c - 1, n, a) > alpha:
        c += 1
    for r in np.arange(1.0, 20, 0.01):
        if binom.sf(c - 1, n, min(r * a, 1)) >= power:
            return float(r)
    return float("nan")


def mcnemar_exact(b, c):
    n = b + c
    return 1.0 if n == 0 else float(min(1.0, 2 * binom.cdf(min(b, c), n, 0.5)))


def load_G(phi):
    """G studies: old full-production CSV (phi 0.8 / 0.95, same seeds) + new tiered runs. Returns df with columns k,p_prod,p_ref,p_shift,tier,forced."""
    parts = []
    old = f"docs/calibration_raw/tail_phi{phi}.csv"
    if os.path.exists(old):
        o = pd.read_csv(old)
        o["tier"] = 1; o["forced"] = True; o["p_pre"] = np.nan; o["p_ref_pre"] = np.nan; o["p_shift"] = np.nan
        sf = f"{RAW}/t3_shiftfill_G_phi{phi}.csv"
        if os.path.exists(sf):
            o = o.drop(columns=["p_shift"]).merge(pd.read_csv(sf)[["k", "p_shift"]], on="k", how="left")
        parts.append(o[["k", "p_prod", "p_ref", "p_shift", "tier", "forced", "p_pre", "p_ref_pre"]])
    for f in (f"{RAW}/t3_G_phi{phi}.csv", f"{RAW}/t3_G_phi{phi}_ext.csv"):
        if os.path.exists(f):
            d = pd.read_csv(f)
            cfg = json.load(open(f.replace(".csv", ".config.json")))
            d["forced"] = (d.k >= cfg["k_full0"]) & (d.k < cfg["k_full0"] + cfg["n_full"])
            parts.append(d[["k", "p_prod", "p_ref", "p_shift", "tier", "forced", "p_pre", "p_ref_pre"]])
    return pd.concat(parts).drop_duplicates("k").sort_values("k").reset_index(drop=True) if parts else None


def load_mode(mode, phi):
    f = f"{RAW}/t3_{mode}_phi{phi}.csv"
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    cfg = json.load(open(f.replace(".csv", ".config.json")))
    d["forced"] = (d.k >= cfg["k_full0"]) & (d.k < cfg["k_full0"] + cfg["n_full"])
    return d


def attach_bc(d, mode, phi):
    f = f"{RAW}/t2bc_{mode}_phi{phi}.csv"
    if d is None or not os.path.exists(f):
        return d
    b = pd.read_csv(f)
    return d.merge(b[["k", "p_bc_pre", "p_bc", "tier"]].rename(columns={"tier": "bc_tier"}), on="k", how="left")


BC_NFULL = 3000


def rate_rows(d, mode, phi, col, pre=None, tiered=True):
    """Counts for p-type `col`. For a<=0.01 all studies with a known pre-screen/decision are used (unknown full p => p>0.01 by the tier rule);
    for a in (0.10,0.05) only the `forced` subset (full p computed for every study)."""
    rows = []
    for a in LEVELS:
        if a >= 0.05:
            x = d[d.forced & d[col].notna() & ((d.k < BC_NFULL) if col == "p_bc" else True)]
            n = len(x); k = int((x[col] <= a).sum())
        else:
            if pre is None:
                x = d[d[col].notna()]; n = len(x); k = int((x[col] <= a).sum())
            else:
                x = d[d[pre].notna() | d[col].notna()]; n = len(x); k = int((x[col].fillna(1.0) <= a).sum())
        if n == 0:
            continue
        lo, hi = cp(k, n)
        rows.append({"mode": mode, "phi": phi, "p_type": col, "level": a, "n_studies": n, "exceed": k, "rate": k / n, "nominal": a, "ratio": k / n / a,
                     "ci_lo": lo, "ci_hi": hi, "ratio_ci_lo": lo / a, "ratio_ci_hi": hi / a, "mdr80": mdr80(n, a),
                     "verdict": ("ANTI-CONSERVATIVE" if lo > a else "conservative" if hi < a else ("consistent with nominal (CI contains it)" if hi / a <= 1.6 else "NOT RESOLVED (CI too wide)"))})
    return rows


def paired(d, mode, phi, c1, c2, pre1, pre2):
    out = []
    for a in LEVELS:
        if a >= 0.05:
            x = d[d.forced & d[c1].notna() & d[c2].notna() & ((d.k < BC_NFULL) if "p_bc" in (c1, c2) else True)]
            i1, i2 = (x[c1] <= a), (x[c2] <= a)
        else:
            x = d[(d[pre1].notna() | d[c1].notna()) & (d[pre2].notna() | d[c2].notna())] if pre1 else d[d[c1].notna() & d[c2].notna()]
            i1, i2 = (x[c1].fillna(1.0) <= a), (x[c2].fillna(1.0) <= a)
        b, c = int((i1 & ~i2).sum()), int((~i1 & i2).sum())
        both = int((i1 & i2).sum()); n = len(x)
        rng = np.random.default_rng(1)
        ms = rng.multinomial(n, [both / n, b / n, c / n, max(0.0, 1 - (both + b + c) / n)], size=4000) if n else np.zeros((1, 4))
        with np.errstate(divide="ignore", invalid="ignore"):
            rr = (ms[:, 0] + ms[:, 1]) / (ms[:, 0] + ms[:, 2])
        rr = rr[np.isfinite(rr)]
        out.append({"mode": mode, "phi": phi, "pair": f"{c1} vs {c2}", "level": a, "n": n, f"{c1}_only": b, f"{c2}_only": c, "both": both, "mcnemar_exact_p": mcnemar_exact(b, c),
                    "count_ratio_first_over_second": (both + b) / max(both + c, 1), "ratio_ci_lo": float(np.percentile(rr, 2.5)) if len(rr) else float("nan"), "ratio_ci_hi": float(np.percentile(rr, 97.5)) if len(rr) else float("nan")})
    return out


def main():
    rows, pr = [], []
    summ = {}
    for phi in (0.0, 0.5, 0.8, 0.95):
        dG = load_G(phi)
        if dG is not None and len(dG):
            dG = attach_bc(dG, "G", phi)
            rows += rate_rows(dG, "G", phi, "p_prod", pre="p_pre", tiered=True)
            rows += rate_rows(dG, "G", phi, "p_ref", pre="p_ref_pre")
            if dG.p_shift.notna().any():
                rows += rate_rows(dG, "G", phi, "p_shift")
            if "p_bc" in dG:
                rows += rate_rows(dG, "G", phi, "p_bc", pre="p_bc_pre")
                pr += paired(dG, "G", phi, "p_prod", "p_bc", "p_pre", "p_bc_pre")
            pr += paired(dG, "G", phi, "p_prod", "p_ref", "p_pre", "p_ref_pre")
            # justification of the tier rule: pre-screen > cut implies production p > 0.01
            chk = dG[dG.forced & dG.p_pre.notna()]
            summ.setdefault("tier_rule_check", {})[f"G_phi{phi}"] = {"forced_studies_with_pre": int(len(chk)), "pre>0.02_but_prod<=0.01": int(((chk.p_pre > PRE_CUT) & (chk.p_prod <= 0.01)).sum())}
        for mode in ("S", "C", "R", "W"):
            d = load_mode(mode, phi)
            if d is None:
                continue
            d = attach_bc(d, mode, phi)
            rows += rate_rows(d, mode, phi, "p_prod", pre="p_pre")
            if mode == "W":
                rows += rate_rows(d, mode, phi, "p_ref", pre="p_ref_pre")
                pr += paired(d, mode, phi, "p_prod", "p_ref", "p_pre", "p_ref_pre")
            if "p_bc" in d and mode != "W":
                pass
            if mode in ("W", "C", "R", "S") and "p_bc" in d:
                pr += paired(d, mode, phi, "p_prod", "p_bc", "p_pre", "p_bc_pre")
            if d.p_shift.notna().any():
                rows += rate_rows(d, mode, phi, "p_shift")
            if "p_bc" in d:
                rows += rate_rows(d, mode, phi, "p_bc", pre="p_bc_pre")
            if mode == "S":
                summ.setdefault("S_template_preserved_share", {})[phi] = float(d.template_preserved.mean())
    T = pd.DataFrame(rows)
    P = pd.DataFrame(pr)
    os.makedirs("docs/audit", exist_ok=True)
    T.to_csv("docs/audit/t3_tail_table.csv", index=False); P.to_csv("docs/audit/t3_paired_table.csv", index=False)
    summ["table"] = T.to_dict(orient="records"); summ["paired"] = P.to_dict(orient="records")
    json.dump(summ, open("docs/audit/t3_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    if len(T):
        print(T[["mode", "phi", "p_type", "level", "n_studies", "exceed", "rate", "ratio", "ratio_ci_lo", "ratio_ci_hi", "mdr80", "verdict"]].round(3).to_string())
    if len(P):
        print(P.round(4).to_string())


if __name__ == "__main__":
    main()
