"""Metrics, cluster bootstrap, multiple-testing correction, regime labels."""
from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown_R(r: np.ndarray) -> float:
    if len(r) == 0:
        return 0.0
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(np.r_[0.0, eq])[1:]
    return float((peak - eq).max())


def max_losing_streak(r: np.ndarray) -> int:
    best = cur = 0
    for x in r:
        cur = cur + 1 if x <= 0 else 0
        best = max(best, cur)
    return best


def profit_factor(r: np.ndarray) -> float:
    w, l = r[r > 0].sum(), -r[r < 0].sum()
    return float("inf") if l == 0 and w > 0 else (float(w / l) if l > 0 else float("nan"))


def trade_metrics(trades: pd.DataFrame, r_col: str = "net_R") -> dict:
    """Required metric set. Everything is after costs unless the key says gross."""
    if trades is None or len(trades) == 0:
        return {"n_trades": 0}
    r = trades[r_col].to_numpy(float)
    wins, losses = r[r > 0], r[r < 0]
    srt = np.sort(r)[::-1]
    ex_top5 = float(srt[5:].mean()) if len(srt) > 5 else float("nan")
    out = {
        "n_trades": int(len(r)),
        "win_rate": float((r > 0).mean()),
        "profit_factor_net": profit_factor(r),
        "expectancy_R_net": float(r.mean()),
        "avg_win_R": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_R": float(losses.mean()) if len(losses) else 0.0,
        "total_R_net": float(r.sum()),
        "max_drawdown_R": max_drawdown_R(r),
        "max_losing_streak": max_losing_streak(r),
        "avg_bars_held": float(trades["bars_held"].mean()) if "bars_held" in trades else float("nan"),
        "expectancy_ex_top5_R": ex_top5,
        "top5_share_of_profit": float(srt[:5].sum() / r.sum()) if r.sum() > 0 and len(srt) >= 5 else float("nan"),
    }
    if "gross_R" in trades:
        out["expectancy_R_gross"] = float(trades["gross_R"].mean())
        out["avg_cost_R"] = float(trades["cost_R"].mean())
        out["median_cost_pct_of_stop"] = float(trades["cost_pct_of_stop"].median())
        out["p90_cost_pct_of_stop"] = float(trades["cost_pct_of_stop"].quantile(0.9))
    return out


def by_year(trades: pd.DataFrame, r_col: str = "net_R") -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame()
    g = trades.groupby(pd.to_datetime(trades["entry_time"]).dt.year)[r_col]
    return pd.DataFrame({"n": g.size(), "expectancy_R": g.mean(), "total_R": g.sum(),
                         "win_rate": g.apply(lambda x: (x > 0).mean())})


def positive_year_share(trades: pd.DataFrame) -> float:
    y = by_year(trades)
    return float((y["expectancy_R"] > 0).mean()) if len(y) else float("nan")


# --------------------------------------------------------------------------- bootstrap
def _clusters(trades: pd.DataFrame, kind: str = "month") -> np.ndarray:
    t = pd.to_datetime(trades["entry_time"])
    key = t.dt.to_period("M") if kind == "month" else t.dt.to_period("Y")
    return pd.factorize(key)[0]


def cluster_bootstrap(trades: pd.DataFrame, n: int = 5000, seed: int = 12345, kind: str = "month",
                      r_col: str = "net_R") -> dict:
    """Resample whole calendar clusters (default: months) to respect serial dependence.

    Returns the 95% CI of mean R and a one-sided p-value for H0: mean <= 0 (null built by centering).
    """
    if len(trades) < 2:
        return {"ci_low": float("nan"), "ci_high": float("nan"), "p_raw": float("nan")}
    r = trades[r_col].to_numpy(float)
    cl = _clusters(trades, kind)
    k = cl.max() + 1
    sums = np.bincount(cl, weights=r, minlength=k)
    cnts = np.bincount(cl, minlength=k).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(n, k))
    means = sums[idx].sum(1) / np.maximum(cnts[idx].sum(1), 1)
    obs = r.mean()
    null = means - obs
    p = (1 + int((null >= obs).sum())) / (1 + n)
    return {"ci_low": float(np.percentile(means, 2.5)), "ci_high": float(np.percentile(means, 97.5)), "p_raw": float(p)}


# --------------------------------------------------------------------------- multiple testing
def bonferroni(p: np.ndarray, m: int | None = None) -> np.ndarray:
    p = np.asarray(p, float)
    m = m or len(p)
    return np.minimum(p * m, 1.0)


def holm(p: np.ndarray, m: int | None = None) -> np.ndarray:
    """Holm step-down. If m > len(p), the missing tests (all other logged trials) are treated as having p=1."""
    p = np.asarray(p, float)
    m = max(m or len(p), len(p))
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj


def benjamini_hochberg(p: np.ndarray, m: int | None = None) -> np.ndarray:
    p = np.asarray(p, float)
    m = max(m or len(p), len(p))
    order = np.argsort(p)[::-1]
    adj = np.empty_like(p)
    running = 1.0
    for rank_desc, i in enumerate(order):
        rank = len(p) - rank_desc
        running = min(running, p[i] * m / rank)
        adj[i] = min(running, 1.0)
    return adj


def adjust_p(p_raw: float, m_trials: int, method: str = "holm") -> float:
    """Adjust ONE p-value for a family of m_trials logged trials (conservative: others assumed p=1)."""
    if not np.isfinite(p_raw):
        return float("nan")
    m = max(int(m_trials), 1)
    return float(min(p_raw * m, 1.0))  # Holm for the smallest p equals Bonferroni with m; larger p's are only more conservative


# --------------------------------------------------------------------------- regimes (past-only labels)
def label_regimes(df: pd.DataFrame, n_trend: int = 50, n_vol: int = 14) -> pd.DataFrame:
    """Per-bar regime labels using only information up to that bar (fixed definitions, set before testing).

    trend: bull / bear / range from the 50-bar efficiency ratio and direction of the 50-bar move
    vol:   high / low from ATR(14) vs its expanding median (past only)
    """
    c = df["close"].astype(float)
    chg = c - c.shift(n_trend)
    path = c.diff().abs().rolling(n_trend).sum()
    er = (chg.abs() / path).fillna(0)
    trend = np.where(er < 0.20, "range", np.where(chg > 0, "bull", "bear"))
    from .engine import atr
    a = pd.Series(atr(df, n_vol), index=df.index)
    med = a.expanding(min_periods=100).median()
    vol = np.where(a > med, "high_vol", "low_vol")
    vol = np.where(a.isna() | med.isna(), "na", vol)
    trend = np.where(chg.isna(), "na", trend)
    return pd.DataFrame({"trend": trend, "vol": vol}, index=df.index)


def by_regime(trades: pd.DataFrame, labels: pd.DataFrame, col: str) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame()
    lab = labels[col].to_numpy()[trades["signal_bar"].to_numpy()]
    g = trades.assign(regime=lab).groupby("regime")["net_R"]
    return pd.DataFrame({"n": g.size(), "expectancy_R": g.mean(), "total_R": g.sum()})
