"""Task 4: calibration of the production monthly cluster bootstrap p-value under a TRUE null (mean R = 0). SYNTHETIC ONLY.

`fast_pvals` is a batched re-implementation of stats.cluster_bootstrap's p_raw (same fixed index matrix idx = default_rng(seed).integers(0,K,(n,K)),
ratio-of-sums mean, centred null, p=(1+#(null>=obs))/(1+n)); `tests/test_audit_bootstrap_equiv.py` checks it equals the production function
on random datasets."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..stats import cluster_bootstrap

_IDX_CACHE: dict = {}


def prod_idx(K: int, n: int = 5000, seed: int = 12345) -> np.ndarray:
    key = (K, n, seed)
    if key not in _IDX_CACHE:
        _IDX_CACHE[key] = np.random.default_rng(seed).integers(0, K, size=(n, K))
    return _IDX_CACHE[key]


def fast_p(sums: np.ndarray, cnts: np.ndarray, n: int = 5000, seed: int = 12345, idx: np.ndarray | None = None) -> float:
    K = len(sums)
    idx = prod_idx(K, n, seed) if idx is None else idx
    means = sums[idx].sum(1) / np.maximum(cnts[idx].sum(1), 1)
    obs = sums.sum() / cnts.sum()
    return (1 + int(((means - obs) >= obs).sum())) / (1 + len(means))


def production_p(r: np.ndarray, month_id: np.ndarray, n=5000, seed=12345) -> float:
    t = pd.Timestamp("2023-01-01") + pd.to_timedelta(month_id * 31, unit="D") + pd.to_timedelta(np.arange(len(r)), unit="m")
    tr = pd.DataFrame({"entry_time": t, "net_R": r})
    return cluster_bootstrap(tr, n, seed, "month")["p_raw"]


# ------------------------------------------------------------------ null data generating processes (all have E[R] = 0 exactly)
@dataclass(frozen=True)
class Scenario:
    name: str
    K: int = 24                     # calendar months in the window (VALID = 24, DEV = 60)
    n_per_month: float = 5.0        # mean trades per active month
    month_dist: str = "equal"       # equal | poisson | negbin (overdispersed) | sparse (30% of months empty, rest dense)
    r_dist: str = "normal"          # normal | rr2 (win +2 w.p. 1/3 else -1) | rr3 (win +3 w.p. 1/4) | t3 (student t, 3 df)
    phi_trade: float = 0.0          # AR(1) between consecutive trades (latent gaussian, rank-transformed to r_dist)
    month_effect: float = 0.0       # sd of a zero-mean month random effect (shared by trades of a month), in units of the trade sd
    phi_month: float = 0.0          # AR(1) of the month effect across months (serial dependence BETWEEN clusters)
    vol_sd: float = 0.0             # sd of log monthly volatility (heteroskedastic months), scale applied to r
    streaks: float = 0.0            # 0..1 persistence of a 2-state win/loss-streak regime (zero-mean regimes)


def _r_transform(z: np.ndarray, dist: str) -> np.ndarray:
    """map standard-normal-marginal latent z to a zero-mean trade R with the requested marginal."""
    from scipy.stats import norm, t as tdist
    u = norm.cdf(z)
    if dist == "normal":
        return z
    if dist == "rr2":
        return np.where(u > 2 / 3, 2.0, -1.0)
    if dist == "rr3":
        return np.where(u > 3 / 4, 3.0, -1.0)
    if dist == "t3":
        return tdist.ppf(u, 3) / np.sqrt(3.0)
    raise ValueError(dist)


def simulate_trades(sc: Scenario, rng) -> tuple[np.ndarray, np.ndarray]:
    """Returns (r, month_id) for one synthetic strategy history under H0."""
    K = sc.K
    if sc.month_dist == "equal":
        cnt = np.full(K, max(1, int(round(sc.n_per_month))))
    elif sc.month_dist == "poisson":
        cnt = rng.poisson(sc.n_per_month, K)
    elif sc.month_dist == "negbin":
        lam = rng.gamma(shape=1.0, scale=sc.n_per_month, size=K)       # strongly overdispersed
        cnt = rng.poisson(lam)
    elif sc.month_dist == "sparse":
        act = rng.random(K) > 0.30
        cnt = np.where(act, rng.poisson(sc.n_per_month / 0.7, K), 0)
    else:
        raise ValueError(sc.month_dist)
    if cnt.sum() < 2:
        cnt[:2] = 1
    month_id = np.repeat(np.arange(K), cnt)
    n = len(month_id)
    # latent gaussian with AR(1) across trades
    e = rng.normal(size=n)
    z = e.copy()
    if sc.phi_trade:
        s = np.sqrt(1 - sc.phi_trade ** 2)
        z[0] = e[0]
        for i in range(1, n):
            z[i] = sc.phi_trade * z[i - 1] + s * e[i]
    r = _r_transform(z, sc.r_dist)
    r = (r - r.mean()) * 0 + r                      # marginal already mean zero
    if sc.streaks:
        # persistent 2-state regime with zero mean (+/-): trades inherit the regime sign => runs of profits then runs of losses
        st = np.empty(n)
        cur = 1.0 if rng.random() < 0.5 else -1.0
        for i in range(n):
            if rng.random() > sc.streaks:
                cur = -cur
            st[i] = cur
        r = r + 0.5 * st
    if sc.month_effect:
        me = np.zeros(K)
        ee = rng.normal(size=K)
        for m in range(K):
            me[m] = (sc.phi_month * me[m - 1] if m else 0.0) + np.sqrt(1 - sc.phi_month ** 2) * ee[m]
        r = r + sc.month_effect * me[month_id]
    if sc.vol_sd:
        r = r * np.exp(sc.vol_sd * rng.normal(size=K))[month_id]
    # exact zero-mean at the population level is by construction; do NOT recentre the sample (that would bias the null)
    return r, month_id


def month_sums(r, month_id):
    keep = np.unique(month_id)                         # production clusters = months that contain at least one trade
    inv = np.searchsorted(keep, month_id)
    return np.bincount(inv, weights=r, minlength=len(keep)), np.bincount(inv, minlength=len(keep)).astype(float)


# ------------------------------------------------------------------ families of m dependent NULL strategies (Holm / FWER study)
def _counts(sc: Scenario, rng) -> np.ndarray:
    K = sc.K
    if sc.month_dist == "equal":
        cnt = np.full(K, max(1, int(round(sc.n_per_month))))
    elif sc.month_dist == "poisson":
        cnt = rng.poisson(sc.n_per_month, K)
    elif sc.month_dist == "negbin":
        cnt = rng.poisson(rng.gamma(shape=1.0, scale=sc.n_per_month, size=K))
    else:
        act = rng.random(K) > 0.30
        cnt = np.where(act, rng.poisson(sc.n_per_month / 0.7, K), 0)
    if cnt.sum() < 2:
        cnt[:2] = 1
    return cnt


def _latent(m: int, n: int, phi: float, rng) -> np.ndarray:
    e = rng.normal(size=(m, n))
    if not phi:
        return e
    z = e.copy()
    s = np.sqrt(1 - phi ** 2)
    for i in range(1, n):
        z[:, i] = phi * z[:, i - 1] + s * e[:, i]
    return z


def simulate_family(sc: Scenario, m: int, rho: float, rng) -> tuple[np.ndarray, np.ndarray]:
    """m null strategies observed on the SAME trade timeline (same months, same trade slots). Trade-level latent = sqrt(rho)*common + sqrt(1-rho)*own;
    month effects, volatility factors and streak regimes (when the scenario has them) are shared by all strategies (market-wide)."""
    cnt = _counts(sc, rng)
    month_id = np.repeat(np.arange(sc.K), cnt)
    n = len(month_id)
    zc = _latent(1, n, sc.phi_trade, rng)
    z = np.sqrt(rho) * zc + np.sqrt(1 - rho) * _latent(m, n, sc.phi_trade, rng)
    r = np.vstack([_r_transform(z[i], sc.r_dist) for i in range(m)])
    if sc.streaks:
        st = np.empty(n); cur = 1.0 if rng.random() < 0.5 else -1.0
        for i in range(n):
            if rng.random() > sc.streaks:
                cur = -cur
            st[i] = cur
        r = r + 0.5 * st[None, :]
    if sc.month_effect:
        ee = rng.normal(size=sc.K); me = np.zeros(sc.K)
        for k in range(sc.K):
            me[k] = (sc.phi_month * me[k - 1] if k else 0.0) + np.sqrt(1 - sc.phi_month ** 2) * ee[k]
        r = r + sc.month_effect * me[month_id][None, :]
    if sc.vol_sd:
        r = r * np.exp(sc.vol_sd * rng.normal(size=sc.K))[month_id][None, :]
    return r, month_id


def family_pvals(r: np.ndarray, month_id: np.ndarray, common_idx: bool = True, rng=None, n: int = 5000) -> np.ndarray:
    keep = np.unique(month_id); inv = np.searchsorted(keep, month_id); K = len(keep)
    cnt = np.bincount(inv, minlength=K).astype(float)
    S = np.vstack([np.bincount(inv, weights=ri, minlength=K) for ri in r])
    obs = S.sum(1) / cnt.sum()
    out = np.empty(len(r))
    if common_idx:
        idx = prod_idx(K, n)
        means = S[:, idx].sum(2) / np.maximum(cnt[idx].sum(1), 1)[None, :]
        return (1 + ((means - obs[:, None]) >= obs[:, None]).sum(1)) / (1 + n)
    for i in range(len(r)):
        idx = rng.integers(0, K, size=(n, K))
        mi = S[i][idx].sum(1) / np.maximum(cnt[idx].sum(1), 1)
        out[i] = (1 + int(((mi - obs[i]) >= obs[i]).sum())) / (1 + n)
    return out
