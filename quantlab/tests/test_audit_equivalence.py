"""Audit sampler must reproduce the production sampler exactly (same RNG stream) when all production components are on."""
import numpy as np

from quantlab.audit import sampler as S
from quantlab.audit.synth import make_series
from quantlab.calibration import ar_series
from quantlab.engine import atr
from quantlab.events import _place_chunk, eligible, infer_bar_td, control_means
import pandas as pd


def _template(seed=3, n=1600):
    df = ar_series(n, 0.8, seed)
    a = atr(df, 14)
    td = infer_bar_td(df)
    el = eligible(df, 5, df.time.iloc[0], df.time.iloc[-1] + td, td, a)
    window = np.where(el)[0]
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(window, 90, replace=False))
    idx = idx[np.r_[True, np.diff(idx) >= 5]]
    return df, window, idx


def test_place_shared_equals_production_chunk():
    df, window, idx = _template()
    pf = S.pool_function(df, window, "full")
    pools = [pf(i) for i in idx]
    for seed in (1, 2, 3):
        a, oka = _place_chunk(pools, 500, len(df), 5, np.random.default_rng(seed))
        b, okb = S.place_shared(pools, 500, len(df), 5, np.random.default_rng(seed), "random")
        assert np.array_equal(a, b) and np.array_equal(oka, okb)


def test_control_draws_equal_production_control_means():
    df, window, idx = _template()
    pf = S.pool_function(df, window, "full")
    pools = [pf(i) for i in idx]
    raw = np.random.default_rng(0).normal(size=len(df))
    sides = np.ones(len(idx))
    m1, att, placed = control_means(pools, raw, sides, 3000, len(df), 5, np.random.default_rng(9))
    P, att2, kept, _ = S.control_draws(pools, 3000, len(df), 5, np.random.default_rng(9))
    assert np.allclose(m1, raw[P].mean(axis=1)) and att == att2


def test_perdraw_and_gap_rules():
    df, window, idx = _template()
    pf = S.pool_function(df, window, "none")
    pools = [pf(i) for i in idx]
    P, ok = S.place_perdraw(pools, 300, len(df), 5, np.random.default_rng(1))
    Q = np.sort(P[ok], axis=1)
    assert (np.diff(Q, axis=1) >= 5).all()
    P1, ok1 = S.place_shared(pools, 300, len(df), 1, np.random.default_rng(1), "time")
    Q1 = np.sort(P1[ok1], axis=1)
    assert (np.diff(Q1, axis=1) >= 1).all()
