"""Exact conditional reference by a reversible Markov chain (Besag & Clifford 1989 'serial' construction). SYNTHETIC USE ONLY (audit candidate).

Null model N_U(T): given the template T (strata pool of every event, count k, non-overlap gap g), the event configuration is UNIFORM over all
feasible assignments (slot j -> a bar of its pool, all pairwise distances >= g).  The single-slot Metropolis chain (pick a slot uniformly, propose a
bar uniformly from its pool, accept iff the configuration stays feasible) has a SYMMETRIC proposal, hence is reversible w.r.t. that uniform law.
Serial test: draw J ~ U{0..M}; run J thinned steps backward and M-J forward from the observed configuration (same kernel, by reversibility); the M+1
states have the observed one at an independent uniformly random index J, so the rank of the observed statistic among them is exactly uniform when the
observed configuration ~ N_U(T) - for ANY chain length / mixing speed (mixing only affects power)."""
from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _run(pos, pools_flat, pstart, plen, occ, gap, steps, thin, raw, out, seed):
    np.random.seed(seed)
    k = pos.shape[0]
    n = occ.shape[0]
    s = 0.0
    for j in range(k):
        s += raw[pos[j]]
    for t in range(out.shape[0]):
        for _ in range(thin):
            j = np.random.randint(0, k)
            x = pools_flat[pstart[j] + np.random.randint(0, plen[j])]
            old = pos[j]
            if x == old:
                continue
            ok = True
            for d in range(-(gap - 1), gap):
                y = x + d
                if y >= 0 and y < n:
                    o = occ[y]
                    if o != 0 and o != j + 1:
                        ok = False
                        break
            if ok:
                occ[old] = 0
                occ[x] = j + 1
                pos[j] = x
                s += raw[x] - raw[old]
        out[t] = s / k
    return 0


def bc_pvalue(idx, pools, raw, n_bars, gap, M, thin, rng, seed_base=0):
    """p = (1 + #{states with statistic >= observed}) / (M + 1).  idx: observed positions (slot order = pools order)."""
    k = len(idx)
    plen = np.array([len(p) for p in pools], dtype=np.int64)
    pstart = np.r_[0, np.cumsum(plen)[:-1]].astype(np.int64)
    flat = np.concatenate(pools).astype(np.int64)
    rawf = np.nan_to_num(raw, nan=0.0)
    obs = float(rawf[idx].mean())
    J = int(rng.integers(0, M + 1))
    stats = []
    for nsteps, off in ((J, 1), (M - J, 2)):
        if nsteps == 0:
            continue
        pos = np.asarray(idx, dtype=np.int64).copy()
        occ = np.zeros(n_bars, dtype=np.int64)
        occ[pos] = np.arange(1, k + 1)
        out = np.empty(nsteps)
        _run(pos, flat, pstart, plen, occ, gap, nsteps * thin, thin, rawf, out, int(rng.integers(0, 2**31 - 1)) + off)
        stats.append(out)
    S = np.concatenate(stats)
    return (1 + int((S >= obs).sum())) / (M + 1), obs, S
