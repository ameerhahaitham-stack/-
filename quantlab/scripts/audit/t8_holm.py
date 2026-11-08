"""Supplementary audit T8: decomposition of the family-wise error of Holm over m=82 NULL strategies with the production monthly-bootstrap p-values.
Factors: A within-strategy temporal dependence (none / trade-level AR(0.7) / own month-effect AR(0.5) / own month-effect AR(0.8)),
         B between-strategy dependence rho (shared latent trade noise AND shared month effect: x_i = sqrt(rho) x_common + sqrt(1-rho) x_own),
         C resampling matrix: one COMMON index matrix for all strategies (production: default_rng(12345)) vs INDEPENDENT matrices per strategy,
         D p-value type: production bootstrap vs oracle z-test (calibrated by construction: exactly valid p for this null) -> shows Holm itself is fine.
Holm rejects at least one hypothesis iff min_i p_i <= alpha/m (first step), so FWER = P(min p <= 0.10/82); the full step-down is run via stats.holm on a
subset of families as a cross-check (mismatch counter in the json). K=24 months, n=5 trades/month, rr2 trades.
Raw: docs/audit/raw/t8/{cell}.npz (per-family min p, #raw rejections at 0.10/82 and at 0.10, p matrix of the first 200 families)."""
import argparse, os, sys, json, time
import numpy as np, pandas as pd
from scipy.stats import beta, norm
from scipy.special import ndtr
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootalt import prod_mx, mult_matrix, NB, _ar_cols
from quantlab.stats import holm

SEED0 = 20261122
M, K, NPM = 82, 24, 5
THR = 0.10 / M
WITHIN = {"W0_none": dict(phi_trade=0.0, sig=0.0, phi_month=0.0), "WT_tradeAR0.7": dict(phi_trade=0.7, sig=0.0, phi_month=0.0),
          "WM5_ownMonthAR0.5": dict(phi_trade=0.0, sig=0.5, phi_month=0.5), "WM8_ownMonthAR0.8": dict(phi_trade=0.0, sig=0.5, phi_month=0.8)}
RHOS = (0.0, 0.5, 0.9)


def gen_family(w, rho, F, rng):
    N = K * NPM; mid = np.repeat(np.arange(K), NPM)
    zc = _ar_cols(rng.standard_normal((F, 1, N)), w["phi_trade"]); zo = _ar_cols(rng.standard_normal((F, M, N)), w["phi_trade"])
    z = np.sqrt(rho) * zc + np.sqrt(1 - rho) * zo
    r = np.where(ndtr(z) > 2 / 3, 2.0, -1.0)
    if w["sig"]:
        mc = _ar_cols(rng.standard_normal((F, 1, K)), w["phi_month"]); mo = _ar_cols(rng.standard_normal((F, M, K)), w["phi_month"])
        r = r + w["sig"] * (np.sqrt(rho) * mc + np.sqrt(1 - rho) * mo)[:, :, mid]
    return r.reshape(F, M, K, NPM).sum(3)


_INDEP = None
def indep_stack():
    global _INDEP
    if _INDEP is None:
        rng = np.random.default_rng([SEED0, 999])
        _INDEP = np.stack([mult_matrix(rng.integers(0, K, size=(NB, K)), K) for _ in range(M)])      # (M, NB, K)
    return _INDEP


def boot_p(S, common):
    F = S.shape[0]; N = K * NPM
    tot = S.sum(2); obs = (tot / N)                                   # (F, M)
    if common:
        sb = np.einsum("fmk,nk->fmn", S, prod_mx(K), optimize=True) / N
    else:
        sb = np.matmul(S.transpose(1, 0, 2), indep_stack().transpose(0, 2, 1)).transpose(1, 0, 2) / N     # (F, M, NB)
    return (1 + ((sb - obs[:, :, None]) >= obs[:, :, None]).sum(2)) / (1 + NB)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--fams", type=int, default=5000); ap.add_argument("--out", default="docs/audit/raw/t8")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    json.dump({"seed0": SEED0, "m": M, "K": K, "n_per_month": NPM, "fams": a.fams, "within": WITHIN, "rhos": RHOS, "thr": THR}, open(f"{a.out}/t8_config.json", "w"), indent=1)
    rows = []; mism = 0; checked = 0
    for wi, (wn, w) in enumerate(WITHIN.items()):
        # oracle sd of the month-total mean for this within-structure (marginal law does not depend on rho: each strategy marginally identical)
        sd = float(np.std(gen_family(w, 0.0, 1000, np.random.default_rng([SEED0, wi, 7])).mean(2).ravel()))
        for ri, rho in enumerate(RHOS):
            for common in (True, False):
                for ptype in ("boot", "oracle"):
                    if ptype == "oracle" and not common:
                        continue
                    cell = f"{wn}_rho{rho}_{'common' if common else 'indep'}_{ptype}"; f = f"{a.out}/{cell}.npz"
                    if not os.path.exists(f):
                        t0 = time.time(); minp, nr, nr10 = [], [], []; keep = None
                        for ci, st in enumerate(range(0, a.fams, 50)):
                            F = min(50, a.fams - st)
                            S = gen_family(w, rho, F, np.random.default_rng([SEED0, wi, ri, ci]))     # same data for boot and oracle cells (same seed)
                            p = boot_p(S, common) if ptype == "boot" else norm.sf((S.mean(2)) / sd)
                            minp.append(p.min(1)); nr.append((p <= THR).sum(1)); nr10.append((p <= 0.10).sum(1))
                            if keep is None:
                                keep = p[:min(F, 50)]
                        minp, nr, nr10 = map(np.concatenate, (minp, nr, nr10))
                        np.savez_compressed(f, minp=minp, nrej=nr, nrej10=nr10, p_first_fams=keep)
                        print(cell, f"{time.time()-t0:.0f}s", flush=True)
                    d = np.load(f); n = len(d["minp"])
                    x = int((d["minp"] <= THR).sum()); lo = beta.ppf(.025, x, n - x + 1) if x else 0.0; hi = beta.ppf(.975, x + 1, n - x)
                    q = d["nrej"].mean() / M
                    rows.append(dict(within=wn, rho=rho, idx="common" if common else "indep", p_type=ptype, fams=n, fwer=x / n, ci_lo=lo, ci_hi=hi, mean_false_rej=float(d["nrej"].mean()),
                                     var_over_mean=float(d["nrej"].var() / max(d["nrej"].mean(), 1e-12)), per_test_rate=float(q), per_test_ratio=float(q / THR),
                                     fwer_if_independent=float(1 - (1 - q) ** M), raw10_rate=float(d["nrej10"].mean() / M)))
                    if ptype == "boot":                                # cross-check the full Holm step-down on up to 200 stored families
                        for pv in d["p_first_fams"][:50]:
                            rej_full = bool((holm(pv) <= 0.10).any()); rej_first = bool(pv.min() <= THR); checked += 1; mism += int(rej_full != rej_first)
    pd.DataFrame(rows).to_csv("docs/audit/t8_holm_decomposition.csv", index=False)
    json.dump({"holm_stepdown_vs_first_step_checked": checked, "mismatches": mism}, open("docs/audit/t8_holm_check.json", "w"))
