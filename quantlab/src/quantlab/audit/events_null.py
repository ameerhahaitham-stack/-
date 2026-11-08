"""Null event-set generators (positions only, independent of returns) for the audit. All return sorted int arrays."""
from __future__ import annotations

import numpy as np

from ..calibration import dedupe_mask


def gen_G(rng, lo: int, hi: int, n_raw: int, gap: int = 5) -> np.ndarray:
    """The calibration's null event process G: n_raw iid uniform bars, sorted, greedy time-ordered de-duplication."""
    x = np.sort(rng.integers(lo, hi, size=(1, n_raw)), axis=1)
    m = dedupe_mask(x, gap)
    return x[0][m[0]]


def gen_G_given_k(rng, lo, hi, n_raw, gap, k, max_tries=400):
    """G conditioned on the de-duplicated count being exactly k (rejection)."""
    for _ in range(max_tries):
        e = gen_G(rng, lo, hi, n_raw, gap)
        if len(e) == k:
            return e
    return None


def gen_clustered(rng, lo, hi, k_target, gap=5, mean_cluster=4, spread=12):
    """Neyman-Scott style clustering (signals arrive in bursts), then greedy de-dup; ~k_target events."""
    out = []
    n_par = max(1, int(k_target * 1.6 / mean_cluster))
    parents = rng.integers(lo, hi, size=n_par)
    for p in parents:
        m = 1 + rng.poisson(mean_cluster - 1)
        out.extend(np.clip(p + rng.integers(-spread, spread + 1, size=m), lo, hi - 1))
    x = np.sort(np.array(out))[None, :]
    return x[0][dedupe_mask(x, gap)[0]]


def gen_regular(rng, lo, hi, k_target, gap=5, jitter=2):
    """Quasi-periodic events (e.g. a time-of-day rule): spacing ~ (hi-lo)/k with small jitter, never closer than `gap`."""
    step = (hi - lo) / k_target
    base = lo + step * (np.arange(k_target) + rng.random())
    x = np.sort(np.clip(np.round(base + rng.integers(-jitter, jitter + 1, size=k_target)).astype(int), lo, hi - 1))[None, :]
    return x[0][dedupe_mask(x, gap)[0]]
