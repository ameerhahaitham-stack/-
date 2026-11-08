"""Audit re-implementation of the event-study control sampler with ablation switches. SYNTHETIC USE ONLY; production code untouched.

`place_shared` is a line-by-line copy of events._place_chunk with the gap generalised (gap 0 = independent draws with repeats allowed,
gap 1 = no repeated bar, gap >= 2 = production rule) and an `order` switch; with order='random', gap=5 and the same RNG it returns
EXACTLY the production picks (verified by tests/test_audit_equivalence.py). `place_perdraw` gives every draw its own random placement
order (production uses one random order shared by the 2000 draws of a chunk)."""
from __future__ import annotations

import numpy as np

from ..engine import _control_pools, strata_labels


def pool_function(df, window, mode: str, min_stratum: int = 5, strata=None):
    """Return pool_for(i) -> array of candidate bars for an event at bar i.
    modes: 'full' (production: year x slot x vol, fall back year x slot, slot, window), 'none' (whole window), 'hour', 'vol', 'year',
    'year_hour' (production minus vol)."""
    year, slot, vol = strata if strata is not None else strata_labels(df)
    if mode == "full":
        pools, _, _, _ = _control_pools(df, window, strata=(year, slot, vol))

        def pool_for(i):
            for key in ((int(year[i]), int(slot[i]), vol[i]), (int(year[i]), int(slot[i])), (int(slot[i]),)):
                cand = pools.get(key)
                if cand is not None and len(cand) >= min_stratum:
                    return cand
            return window
        return pool_for
    if mode == "none":
        return lambda i: window
    keyf = {"hour": lambda i: int(slot[i]), "vol": lambda i: vol[i], "year": lambda i: int(year[i]),
            "year_hour": lambda i: (int(year[i]), int(slot[i]))}[mode]
    pools: dict = {}
    for i in window:
        pools.setdefault(keyf(i), []).append(int(i))
    pools = {k: np.array(v) for k, v in pools.items()}

    def pool_for(i):
        cand = pools.get(keyf(i))
        return cand if cand is not None and len(cand) >= min_stratum else window
    return pool_for


def place_shared(pools, n_draws, n_bars, gap, rng, order="random", max_tries=40):
    """Copy of events._place_chunk. order: 'random' (rng.permutation, production), 'time' (event order as given = chronological),
    'reverse'."""
    k = len(pools)
    picks = np.full((n_draws, k), -1, dtype=np.int64)
    blocked = np.zeros((n_draws, n_bars), dtype=bool)
    ok = np.ones(n_draws, dtype=bool)
    rows_all = np.arange(n_draws)
    offs = np.arange(-(gap - 1), gap) if gap >= 1 else np.array([0])
    seq = rng.permutation(k) if order == "random" else (np.arange(k) if order == "time" else np.arange(k)[::-1])
    for j in seq:
        pool = pools[j]
        if gap == 0:                                   # independent draws, repeats allowed
            picks[:, j] = pool[rng.integers(0, len(pool), size=n_draws)]
            continue
        todo = rows_all[ok]
        cand = np.full(n_draws, -1, dtype=np.int64)
        for _ in range(max_tries):
            if len(todo) == 0:
                break
            c = pool[rng.integers(0, len(pool), size=len(todo))]
            good = ~blocked[todo, c]
            cand[todo[good]] = c[good]
            todo = todo[~good]
        for d in todo:
            allowed = pool[~blocked[d, pool]]
            if len(allowed) == 0:
                ok[d] = False
            else:
                cand[d] = allowed[rng.integers(0, len(allowed))]
        placed = rows_all[ok & (cand >= 0)]
        picks[placed, j] = cand[placed]
        for off in offs:
            blocked[placed, np.clip(cand[placed] + off, 0, n_bars - 1)] = True
    return picks, ok


def place_perdraw(pools, n_draws, n_bars, gap, rng, max_tries=40):
    """Like place_shared but every draw has its OWN random placement order (CSR pool lookup)."""
    k = len(pools)
    lens = np.array([len(p) for p in pools], dtype=np.int64)
    starts = np.r_[0, np.cumsum(lens)[:-1]]
    flat = np.concatenate(pools)
    perm = np.argsort(rng.random((n_draws, k)), axis=1)
    picks = np.full((n_draws, k), -1, dtype=np.int64)
    blocked = np.zeros((n_draws, n_bars), dtype=bool)
    ok = np.ones(n_draws, dtype=bool)
    rows_all = np.arange(n_draws)
    offs = np.arange(-(gap - 1), gap) if gap >= 1 else np.array([0])
    for r in range(k):
        e = perm[:, r]
        todo = rows_all[ok]
        cand = np.full(n_draws, -1, dtype=np.int64)
        for _ in range(max_tries):
            if len(todo) == 0:
                break
            ee = e[todo]
            c = flat[starts[ee] + (rng.random(len(todo)) * lens[ee]).astype(np.int64)]
            good = ~blocked[todo, c]
            cand[todo[good]] = c[good]
            todo = todo[~good]
        for d in todo:
            pool = pools[e[d]]
            allowed = pool[~blocked[d, pool]]
            if len(allowed) == 0:
                ok[d] = False
            else:
                cand[d] = allowed[rng.integers(0, len(allowed))]
        placed = rows_all[ok & (cand >= 0)]
        picks[placed, e[placed]] = cand[placed]
        for off in offs:
            blocked[placed, np.clip(cand[placed] + off, 0, n_bars - 1)] = True
    return picks, ok


def control_draws(pools, n_draws, n_bars, gap, rng, order="random", retry=True, chunk=2000, budget=4):
    """Return (picks[<=n_draws,k], attempts, kept). retry=True: dead-end draws are discarded and replaced (production). retry=False: a
    single pass of n_draws attempts; dead-end draws are KEPT with their unplaced events dropped (NaN picks)."""
    place = (lambda n: place_perdraw(pools, n, n_bars, gap, rng)) if order == "perdraw" else (lambda n: place_shared(pools, n, n_bars, gap, rng, order))
    out, got, attempts = [], 0, 0
    if not retry:
        picks, ok = place(n_draws)
        return picks, n_draws, int(ok.sum()), ok
    while got < n_draws and attempts < budget * n_draws:
        picks, ok = place(chunk)
        attempts += chunk
        if ok.any():
            out.append(picks[ok])
            got += int(ok.sum())
        elif attempts >= 5 * chunk and got == 0:
            break
    P = np.concatenate(out)[:n_draws] if out else np.empty((0, len(pools)), dtype=np.int64)
    return P, attempts, len(P), np.ones(len(P), bool)


def cov_index(pos_sorted: np.ndarray, phi: float) -> np.ndarray:
    """K = sum_{i<j} phi^{|x_i-x_j|} for each row of SORTED positions: the configuration functional that drives Var(mean of raw moves) under AR(1)."""
    n, k = pos_sorted.shape
    K = np.zeros(n)
    for d in range(1, min(k, 40)):
        diff = (pos_sorted[:, d:] - pos_sorted[:, :-d]).astype(float)
        K += (phi ** diff).sum(axis=1)
    return K


def close_pairs(pos_sorted: np.ndarray, dmax: int) -> np.ndarray:
    """Number of adjacent (in time) event pairs at distance <= dmax."""
    return ((pos_sorted[:, 1:] - pos_sorted[:, :-1]) <= dmax).sum(axis=1)
