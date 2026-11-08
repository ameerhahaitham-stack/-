"""Task 5: null calibration of the trade-vs-matched-control p-value (engine.matched_control). SYNTHETIC ONLY.

Null: strategy signals are placed at bars drawn independently of prices (G with min gap 1: the engine's own concurrency rule then thins them),
sides random, stop/rr/max_hold fixed in ATR units. Under this null the strategy has no timing information, so P(p_vs_control <= a) should be <= a.
`matched_control_audit` is an instrumented copy of the production function (same RNG stream => identical p; verified in
tests/test_audit_trade_equiv.py) that also records the executed-control counts and the pre-subsample distribution."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..calibration import H4, ar_series
from ..costs import ZERO
from ..engine import Signal, _control_pools, atr, run_backtest, strata_labels
from .events_null import gen_G


@dataclass(frozen=True)
class TradeCfg:
    name: str = "phi0.8_mid"
    phi: float = 0.8
    n_raw: int = 70
    k_atr: float = 1.5
    rr: float = 2.0
    max_hold: int = 20
    n_bars: int = 1600
    n_reps: int = 500
    r_ref: int = 500
    series_seed0: int = 1_100_000
    event_seed0: int = 11_000_000
    ref_seed0: int = 13_000_000
    ctrl_seed0: int = 15_000_000
    regular: int = 0                  # >0: signals on a quasi-regular grid (spacing `regular` bars, jitter +-2) instead of G (stress: real trades execute, random controls collide)


def make_signals(df, a, o, idx, sides, cfg):
    return [Signal(int(i), int(s), float(o[i + 1] - s * cfg.k_atr * a[i]), cfg.rr, cfg.max_hold) for i, s in zip(idx, sides)]


def null_signals(df, a, o, cfg, rng):
    if cfg.regular:
        base = np.arange(60 + int(rng.integers(0, cfg.regular)), cfg.n_bars - 50, cfg.regular)
        idx = np.unique(np.clip(base + rng.integers(-2, 3, size=len(base)), 60, cfg.n_bars - 51))
    else:
        idx = gen_G(rng, 60, cfg.n_bars - 50, cfg.n_raw, 1)
    sides = rng.choice([-1, 1], size=len(idx))
    return make_signals(df, a, o, idx, sides, cfg)


def matched_control_audit(df, signals, cm, eval_start, eval_end, n_reps=500, seed=777, min_stratum=5):
    """Line-by-line copy of engine.matched_control (fallback_spread 0) + diagnostics."""
    df = df.reset_index(drop=True)
    a = atr(df, 14)
    t = df["time"]
    es, ee = pd.Timestamp(eval_start), pd.Timestamp(eval_end)
    window = np.where((t >= es).to_numpy() & (t < ee).to_numpy() & ~np.isnan(a))[0]
    window = window[window < len(df) - 1]
    real = run_backtest(df, signals, cm, eval_start, eval_end, 0.0).trades
    if len(real) == 0:
        return None
    pools, year, slot, vol = _control_pools(df, window)
    rng = np.random.default_rng(seed)
    o = df["open"].to_numpy(float)
    by_i = {s.i: s for s in signals}
    spec = []
    for r in real.itertuples():
        i0, e0 = r.signal_bar, r.entry_bar
        if np.isnan(a[i0]) or a[i0] <= 0:
            continue
        sg0 = by_i[i0]
        pool = None
        for key in ((int(year[i0]), int(slot[i0]), vol[i0]), (int(year[i0]), int(slot[i0])), (int(slot[i0]),)):
            cand = pools.get(key)
            if cand is not None and len(cand) >= min_stratum:
                pool = cand
                break
        if pool is None:
            pool = window
        spec.append((r.side, abs(o[e0] - sg0.stop) / a[i0], sg0.rr, sg0.max_hold, pool))
    n_real = len(spec)
    means, n_exec, mean_all, held = [], [], [], []
    for _ in range(n_reps):
        sigs = []
        for (side, k, rr, mh, pool) in spec:
            for i in rng.choice(pool, size=2):
                sigs.append(Signal(int(i), side, o[i + 1] - side * k * a[i], rr, mh))
        res = run_backtest(df, sigs, cm, eval_start, eval_end, 0.0).trades
        if len(res) == 0:
            continue
        n_exec.append(len(res))
        mean_all.append(float(res["net_R"].mean()))
        if len(res) > n_real:
            res = res.iloc[np.sort(rng.choice(len(res), size=n_real, replace=False))]
        means.append(float(res["net_R"].mean()))
        held.append(float(res["bars_held"].mean()))
    return {"real": real, "n_real": n_real, "means": np.array(means), "n_exec": np.array(n_exec), "mean_all": np.array(mean_all), "held": np.array(held)}


def _p(means, obs):
    return (1 + int((means >= obs).sum())) / (1 + len(means)) if len(means) else float("nan")


def trade_study(cfg: TradeCfg, k: int) -> list[dict]:
    df = ar_series(cfg.n_bars, cfg.phi, cfg.series_seed0 + k)
    t = pd.to_datetime(df["time"])
    a, o = atr(df, 14), df["open"].to_numpy(float)
    es, ee = t.iloc[0], t.iloc[-1] + H4
    sigs = null_signals(df, a, o, cfg, np.random.default_rng(cfg.event_seed0 + k))
    out = matched_control_audit(df, sigs, ZERO, es, ee, cfg.n_reps, cfg.ctrl_seed0 + k)
    if out is None:
        return [{"k": k, "n_signals": len(sigs), "n_real": 0}]
    obs = float(out["real"]["net_R"].mean())
    # exact reference: independent draws of the SAME null pipeline (signals -> engine), exchangeable with the observed history
    rr = np.random.default_rng(cfg.ref_seed0 + k)
    ref = []
    for _ in range(cfg.r_ref):
        tr = run_backtest(df, null_signals(df, a, o, cfg, rr), ZERO, es, ee).trades
        if len(tr):
            ref.append(float(tr["net_R"].mean()))
    m, ma = out["means"], out["mean_all"]
    return [{"k": k, "n_signals": len(sigs), "n_real": out["n_real"], "obs": obs, "ctrl_mean": float(m.mean()), "ctrl_sd": float(m.std(ddof=1)),
             "ctrl_all_mean": float(ma.mean()), "ctrl_all_sd": float(ma.std(ddof=1)),
             "p_prod": _p(m, obs), "p_nosub": _p(ma, obs), "p_ref": _p(np.array(ref), obs), "ref_sd": float(np.std(ref, ddof=1)),
             "n_exec_mean": float(out["n_exec"].mean()), "n_exec_min": int(out["n_exec"].min()), "short_frac": float((out["n_exec"] < out["n_real"]).mean()),
             "real_held": float(out["real"]["bars_held"].mean()), "ctrl_held": float(out["held"].mean()), "n_reps_ok": int(len(m))}]


# ---------------------------------------------------------------- supplementary audit: drift-regime null (limits of the random-side null)
def drift_series(n: int, phi: float, seed: int, mu: float, persist: float, sigma: float = 3.0) -> pd.DataFrame:
    """ar_series plus a zero-mean persistent two-state drift (+-mu price units per bar, regime persistence `persist` per bar). The overall mean drift is zero
    but a given 2-year sample is dominated by whichever regime lasted longer: market drift that a fixed-side strategy with NO timing skill harvests."""
    rng = np.random.default_rng(seed)
    e = rng.normal(0, sigma, n)
    st = np.empty(n)
    cur = 1.0 if rng.random() < 0.5 else -1.0
    u = rng.random(n)
    for k in range(n):
        if u[k] > persist:
            cur = -cur
        st[k] = cur
    r = np.zeros(n)
    for k in range(1, n):
        r[k] = phi * r[k - 1] + e[k] + mu * st[k]
    c = 1000 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    return pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + 1, "low": np.minimum(o, c) - 1, "close": c, "tick_volume": 1, "spread": 0, "real_volume": 0})


@dataclass(frozen=True)
class DriftCfg:
    name: str = "D1"
    phi: float = 0.3
    mu: float = 0.3
    persist: float = 0.995
    n_bars: int = 4320
    n_raw: int = 150
    k_atr: float = 1.5
    rr: float = 2.0
    max_hold: int = 20
    n_reps: int = 500
    series_seed0: int = 2_100_000
    event_seed0: int = 12_000_000
    ctrl_seed0: int = 16_000_000


def drift_study(cfg: DriftCfg, k: int) -> list[dict]:
    from ..stats import cluster_bootstrap
    df = drift_series(cfg.n_bars, cfg.phi, cfg.series_seed0 + k, cfg.mu, cfg.persist)
    t = pd.to_datetime(df["time"])
    a, o = atr(df, 14), df["open"].to_numpy(float)
    es, ee = t.iloc[0], t.iloc[-1] + H4
    rng = np.random.default_rng(cfg.event_seed0 + k)
    idx = gen_G(rng, 60, cfg.n_bars - 50, cfg.n_raw, 1)
    sides = np.ones(len(idx), dtype=int)                                   # fixed side: market drift is NOT averaged out
    tc = TradeCfg(k_atr=cfg.k_atr, rr=cfg.rr, max_hold=cfg.max_hold)
    sigs = make_signals(df, a, o, idx, sides, tc)
    out = matched_control_audit(df, sigs, ZERO, es, ee, cfg.n_reps, cfg.ctrl_seed0 + k)
    if out is None:
        return [{"k": k, "n_real": 0}]
    real = out["real"]
    obs = float(real["net_R"].mean())
    bs = cluster_bootstrap(real, 5000, 12345, "month")
    sd = float(real["net_R"].std(ddof=1)); n = len(real)
    return [{"k": k, "n_real": n, "obs": obs, "t_naive": obs / (sd / np.sqrt(n)), "p_boot": bs["p_raw"], "n_clusters": bs["n_clusters"],
             "p_ctrl": _p(out["means"], obs), "ctrl_mean": float(out["means"].mean()), "n_exec_mean": float(out["n_exec"].mean()),
             "drift_exposure": float(np.sign(np.diff(df["close"].to_numpy())).mean())}]
