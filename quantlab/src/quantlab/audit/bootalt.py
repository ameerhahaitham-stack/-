"""Supplementary audit (synthetic only): vectorised null/alternative generator for monthly strategy returns and a panel of p-value methods
evaluated on the SAME datasets. Equal trade count n per calendar month (the empty-month / unequal-count issue is studied separately in gaps.py).

Statistic = mean R per trade = (sum of month totals)/N with N fixed => everything below works on month totals S (reps x K).
Methods (one-sided, H1: mean > 0):
  boot   production cluster_bootstrap p (idx = default_rng(12345).integers(0,K,(5000,K)), centred null, p=(1+#(null>=obs))/(1+n))
  t      Student t on month totals, K-1 df (iid months)
  nw1/nw3 Newey-West (Bartlett) variance, lag 1 / 3, t with K-1 df
  kv     Kiefer-Vogelsang fixed-b: Bartlett kernel with bandwidth = K (b=1); reference distribution simulated under iid N(0,1) at the same K
  imq4/imb6/imb3  Ibragimov-Mueller group test: contiguous blocks (4 blocks / blocks of 6 months / blocks of 3 months), t with q-1 df on block means
  ar1    t with variance inflated by (1+rho)/(1-rho), rho = clipped lag-1 autocorrelation of month totals
  cbb3   circular block bootstrap, block length 3 months, 5000 resamples, centred null
  oracle z test with the TRUE sd of the mean (known only inside the simulation)
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr
from scipy.stats import t as tdist, norm

NB = 5000
_MX: dict = {}


def mult_matrix(idx: np.ndarray, K: int) -> np.ndarray:
    n = idx.shape[0]
    M = np.zeros((n, K), dtype=np.float64)
    np.add.at(M, (np.repeat(np.arange(n), idx.shape[1]), idx.ravel()), 1.0)
    return M


def prod_mx(K: int) -> np.ndarray:
    key = ("prod", K)
    if key not in _MX:
        _MX[key] = mult_matrix(np.random.default_rng(12345).integers(0, K, size=(NB, K)), K)
    return _MX[key]


def cbb_mx(K: int, B: int = 3) -> np.ndarray:
    key = ("cbb", K, B)
    if key not in _MX:
        rng = np.random.default_rng(777)
        nblk = -(-K // B)
        st = rng.integers(0, K, size=(NB, nblk))
        idx = ((st[:, :, None] + np.arange(B)[None, None, :]) % K).reshape(NB, -1)[:, :K]
        _MX[key] = mult_matrix(idx, K)
    return _MX[key]


# ------------------------------------------------------------------ generator
SCEN = {
    # name: dict(r_dist, phi_trade, month_effect, phi_month, vol_sd, phi_vol, streaks, tier)
    "N1_iid_normal":      dict(r="normal", tier="A"),
    "N2_iid_rr2":         dict(r="rr2", tier="A"),
    "T1_tradeAR0.1":      dict(r="rr2", phi_trade=0.1, tier="A"),
    "T2_tradeAR0.3":      dict(r="rr2", phi_trade=0.3, tier="B"),
    "T3_tradeAR0.7":      dict(r="rr2", phi_trade=0.7, tier="C"),
    "M1_monthEff0.5_iid": dict(r="rr2", month_effect=0.5, tier="A"),
    "M4_monthEff0.25_AR0.8": dict(r="rr2", month_effect=0.25, phi_month=0.8, tier="B"),
    "M2_monthEff0.5_AR0.5":  dict(r="rr2", month_effect=0.5, phi_month=0.5, tier="B"),
    "M3_monthEff0.5_AR0.8":  dict(r="rr2", month_effect=0.5, phi_month=0.8, tier="C"),
    "V1_vol0.5_iid":      dict(r="rr2", vol_sd=0.5, tier="A"),
    "V2_vol0.5_AR0.8":    dict(r="rr2", vol_sd=0.5, phi_vol=0.8, tier="B"),
    "V3_vol1.0_iid":      dict(r="rr2", vol_sd=1.0, tier="B"),
    "S1_streak0.9":       dict(r="rr2", streaks=0.9, tier="B"),
}


def _ar_cols(e: np.ndarray, phi: float) -> np.ndarray:
    """AR(1) recursion along the LAST axis (time) for arrays of any rank (reps x time, or families x strategies x time)."""
    if not phi:
        return e
    z = e.copy()
    s = np.sqrt(1 - phi ** 2)
    for i in range(1, e.shape[-1]):
        z[..., i] = phi * z[..., i - 1] + s * e[..., i]
    return z


def gen_month_sums(name: str, K: int, n: int, reps: int, rng, mu: float = 0.0, trades: bool = False):
    """reps x K matrix of month totals of trade R (mean per trade = mu, trade sd about 1.4-1.6) under scenario `name`. trades=True also returns the (reps x K*n) trade R."""
    sc = SCEN[name]
    N = K * n
    z = _ar_cols(rng.standard_normal((reps, N)), sc.get("phi_trade", 0.0))
    d = sc["r"]
    if d == "normal":
        r = z
    elif d == "rr2":
        r = np.where(ndtr(z) > 2 / 3, 2.0, -1.0)
    else:
        raise ValueError(d)
    if sc.get("streaks"):
        flips = rng.random((reps, N)) > sc["streaks"]
        sign = 1 - 2 * (np.cumsum(flips, axis=1) % 2)
        init = np.where(rng.random((reps, 1)) < 0.5, 1.0, -1.0)
        r = r + 0.5 * sign * init
    mid = np.repeat(np.arange(K), n)
    if sc.get("month_effect"):
        me = _ar_cols(rng.standard_normal((reps, K)), sc.get("phi_month", 0.0))
        r = r + sc["month_effect"] * me[:, mid]
    if sc.get("vol_sd"):
        lv = _ar_cols(rng.standard_normal((reps, K)), sc.get("phi_vol", 0.0))
        r = r * np.exp(sc["vol_sd"] * lv)[:, mid]
    S = r.reshape(reps, K, n).sum(2)
    if mu:
        S = S + n * mu                      # shift AFTER summation: keeps integer-lattice sums exact (production ties are rounding-sensitive otherwise)
    return (S, r) if trades else S


# ------------------------------------------------------------------ p-value methods
_KV: dict = {}


def _bartlett_W(K: int) -> np.ndarray:
    i = np.arange(K)
    return 1 - np.abs(i[:, None] - i[None, :]) / K


def kv_ref(K: int, draws: int = 1_000_000, seed: int = 424242) -> np.ndarray:
    """sorted reference sample of the fixed-b (b=1) Bartlett t statistic under iid N(0,1) month totals at this K."""
    if K not in _KV:
        rng = np.random.default_rng([seed, K])
        W = _bartlett_W(K)
        out = np.empty(draws, dtype=np.float32)
        ch = 100_000
        for a in range(0, draws, ch):
            x = rng.standard_normal((ch, K))
            out[a:a + ch] = _kv_stat(x, W)
        _KV[K] = np.sort(out)
    return _KV[K]


def _kv_stat(S: np.ndarray, W: np.ndarray) -> np.ndarray:
    K = S.shape[1]
    m = S.mean(1)
    u = S - m[:, None]
    v = np.einsum("ij,jk,ik->i", u, W, u) / K ** 2
    return m / np.sqrt(np.maximum(v, 1e-300))


def _nw_var(u: np.ndarray, L: int) -> np.ndarray:
    K = u.shape[1]
    v = (u ** 2).sum(1)
    for l in range(1, min(L, K - 1) + 1):
        v = v + 2 * (1 - l / (L + 1)) * (u[:, l:] * u[:, :-l]).sum(1)
    return np.maximum(v, 1e-300) * K / (K - 1) / K ** 2        # variance of the mean of month totals


def _im(S: np.ndarray, q: int) -> np.ndarray:
    K = S.shape[1]
    b = K // q
    g = S[:, : b * q].reshape(S.shape[0], q, b).mean(2)
    t = g.mean(1) / np.sqrt(np.maximum(g.var(1, ddof=1) / q, 1e-300))
    return tdist.sf(t, q - 1)


def all_p(S: np.ndarray, n: int, sd_true: float | None = None) -> dict:
    """p-values (one-sided) of every method for each row of S (month totals, equal trade counts)."""
    reps, K = S.shape
    N = float(K * n)                                          # total trades; bootstrap compares per-trade means exactly as production does
    tot = S.sum(1)
    m = tot / K
    u = S - m[:, None]
    out: dict = {}
    # production bootstrap: means = sum(resampled totals)/count, null = means - obs, p = (1 + #(null >= obs)) / (1 + 5000)
    for name, Mx in (("boot", prod_mx(K)), ("cbb3", cbb_mx(K))):
        p = np.empty(reps)
        for a in range(0, reps, 2000):
            sb = S[a:a + 2000] @ Mx.T / N
            obs = (tot[a:a + 2000] / N)[:, None]
            p[a:a + 2000] = (1 + ((sb - obs) >= obs).sum(1)) / (1 + NB)
        out[name] = p
    v_t = (u ** 2).sum(1) / (K * (K - 1))
    out["t"] = tdist.sf(m / np.sqrt(np.maximum(v_t, 1e-300)), K - 1)
    v1, v3 = _nw_var(u, 1), _nw_var(u, 3)
    out["nw1"] = tdist.sf(m / np.sqrt(v1), K - 1)
    out["nw3"] = tdist.sf(m / np.sqrt(v3), K - 1)
    W = _bartlett_W(K)
    st = _kv_stat(S, W)
    ref = kv_ref(K)
    out["kv"] = np.maximum(1 - np.searchsorted(ref, st, side="left") / len(ref), 0.5 / len(ref))
    ar = np.clip((u[:, 1:] * u[:, :-1]).sum(1) / np.maximum((u ** 2).sum(1), 1e-300), 0.0, 0.95)
    v_ar = v_t * (1 + ar) / (1 - ar)
    out["ar1"] = tdist.sf(m / np.sqrt(v_ar), K - 1)
    out["imq4"] = _im(S, 4)
    out["imb6"] = _im(S, max(K // 6, 2))
    out["imb3"] = _im(S, max(K // 3, 2))
    if sd_true is not None:
        out["oracle"] = norm.sf(m / sd_true)
    # variance estimates of the mean of month totals (for long-run-variance reliability)
    out["_v_boot"] = (u ** 2).sum(1) / K ** 2
    out["_v_t"] = v_t
    out["_v_nw1"], out["_v_nw3"] = v1, v3
    out["_v_kv"] = np.einsum("ij,jk,ik->i", u, W, u) / K ** 2
    out["_v_ar1"] = v_ar
    q = max(K // 6, 2)
    g = S[:, : (K // q) * q].reshape(reps, q, K // q).mean(2)
    out["_v_imb6"] = g.var(1, ddof=1) / q
    out["_m"] = m
    return out
