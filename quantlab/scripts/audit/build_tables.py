"""Builds docs/audit/TABLES.md (all result tables of the report in markdown) from the CSV/JSON produced by the analysis scripts."""
import json, os, glob
import numpy as np, pandas as pd

out = []
def md(df, fmt=3):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else (f"{v:.{fmt}f}" if abs(v) >= 0.01 or v == 0 else f"{v:.2g}"))
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)

# ---- T1
for name in ("phi0.8", "phi0.95", "sv"):
    f = f"docs/audit/t1_table_{name}.csv"
    if os.path.exists(f):
        t = pd.read_csv(f)
        t = t[["config", "n_studies", "ratio0.1", "ratio0.05", "ratio0.01", "var_z", "dvar_z_vs_G", "dvar_se", "sd_ratio_vs_G", "mean_shift_sdG", "K_obs/K_ctrl", "cp7_obs", "cp7_ctrl"]]
        out += [f"### T1 ablation — {name}\n", md(t), ""]
# ---- T3
f = "docs/audit/t3_tail_table.csv"
if os.path.exists(f):
    t = pd.read_csv(f)
    t["ratio [95% CI]"] = t.apply(lambda r: f"{r.ratio:.2f} [{r.ratio_ci_lo:.2f}, {r.ratio_ci_hi:.2f}]", axis=1)
    for (mode, phi), g in t.groupby(["mode", "phi"]):
        piv = g.pivot_table(index="p_type", columns="level", values="ratio [95% CI]", aggfunc="first")
        n = g.pivot_table(index="p_type", columns="level", values="n_studies", aggfunc="first")
        ex = g.pivot_table(index="p_type", columns="level", values="exceed", aggfunc="first")
        comb = piv.copy()
        for i in piv.index:
            for c in piv.columns:
                comb.loc[i, c] = f"{ex.loc[i, c]:.0f}/{n.loc[i, c]:.0f}: {piv.loc[i, c]}"
        comb = comb[sorted(comb.columns, reverse=True)]
        out += [f"### T3 tail calibration — mode {mode}, phi={phi} (cells: exceedances/studies: ratio actual/nominal [exact 95% CI])\n", md(comb.reset_index()), ""]
f = "docs/audit/t3_paired_table.csv"
if os.path.exists(f):
    p = pd.read_csv(f)
    p = p[["mode", "phi", "pair", "level", "n", "both", "count_ratio_first_over_second", "ratio_ci_lo", "ratio_ci_hi", "mcnemar_exact_p"]]
    out += ["### T3 paired comparison of exceedance counts (first p-type / second p-type; McNemar exact)\n", md(p), ""]
# ---- T4
f = "docs/audit/t4_bootstrap_table.csv"
if os.path.exists(f):
    t = pd.read_csv(f)
    cols = ["scenario", "mean_trades", "mean_clusters", "ratio@0.1", "ratio@0.05", "ratio@0.01", "ratio@0.0025", "ratio@0.00125", "lo@0.00125", "hi@0.00125", "share_p_at_min(1/5001)"]
    out += ["### T4 monthly cluster bootstrap, 60000 replications per scenario (ratio = actual/nominal)\n", md(t[cols]), ""]
f = "docs/audit/t4c_table.csv"
if os.path.exists(f):
    t = pd.read_csv(f)
    for a in (0.05, 0.00125):
        out += [f"### T4c ratio actual/nominal at {a} by number of months K (production bootstrap)\n", md(t.pivot(index="scenario", columns="K", values=f"boot@{a}").reset_index()), ""]
    out += ["### T4c design effect = true Var(mean) / mean bootstrap Var(mean)\n", md(t.pivot(index="scenario", columns="K", values="design_effect_true_var/boot_var").reset_index()), ""]
    k24 = t[t.K == 24].set_index("scenario")
    for a in (0.01, 0.00125):
        out += [f"### T4c K=24: ratio at {a} per method\n", md(k24[[f"{m}@{a}" for m in ("boot", "t", "nw", "cbb3", "oracle")]].reset_index()), ""]
f = "docs/audit/t4_resolution_table.csv"
if os.path.exists(f):
    r = pd.read_csv(f); out += ["### T4 decision noise at the 0.00125 threshold (probability of rejecting when the bootstrap-limit p equals p*)\n", md(r[r.n_resamples.isin([5000, 20000, 100000, 1000000])].pivot(index="true_p", columns="n_resamples", values="P_reject_at_0.00125").reset_index(), 3), ""]
f = "docs/audit/t4d_family_table.csv"
if os.path.exists(f):
    t = pd.read_csv(f)[["scenario", "rho_between_strategies", "n_true_effects", "selection", "FWER_holm_0.10", "FWER_ci_lo", "FWER_ci_hi", "mean_false_rejections_after_holm", "mean_false_rejections_raw_p<=0.10/82 (before Holm)", "per_test_false_rate_raw_p<=0.10/82_vs_nominal", "power_holm_true_rejected"]]
    out += ["### 82-family simulations (2500 families each; Holm exactly as registry.family_table)\n", md(t), ""]
# ---- T5
f = "docs/audit/t5_trade_table.csv"
if os.path.exists(f):
    t = pd.read_csv(f)
    cols = ["setting", "n_studies", "mean_real_trades", "mean_exec_controls_before_subsample", "share_reps_with_too_few_controls", "var_z", "p_prod@0.1", "p_prod_lo@0.1", "p_prod_hi@0.1", "p_prod@0.05", "p_prod_lo@0.05", "p_prod_hi@0.05", "p_prod@0.01", "p_nosub@0.1", "p_nosub@0.05", "p_ref@0.1"]
    out += ["### T5 trade-control p (ratio actual/nominal; resolution 1/501)\n", md(t[cols]), ""]
open("docs/audit/TABLES.md", "w").write("\n".join(out))
print(len(out), "blocks")
