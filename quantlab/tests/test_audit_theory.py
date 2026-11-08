"""Exact enumeration check of the lemma used in the audit: the null event process G (n iid uniform bars, sort, greedy de-dup with min gap g)
conditioned on its size k is UNIFORM over all gap-feasible configurations, except that a configuration whose last element sits within g-1 bars of
the end of the domain has a truncated last 'shadow' and proportionally smaller probability.
Count of raw tuples mapping to configuration C:  N(C) = sum_{m=0..k} (-1)^m C(k,m) (|U(C)| - m)^n,  |U(C)| = k*g - t(C)."""
import itertools
from collections import Counter
from math import comb

import numpy as np


def dedupe(sorted_x, g):
    out, last = [], -10**9
    for x in sorted_x:
        if x - last >= g:
            out.append(x); last = x
    return tuple(out)


def test_G_conditional_on_k_is_uniform_up_to_boundary_truncation():
    L, g, n = 11, 3, 5
    cnt = Counter(dedupe(sorted(t), g) for t in itertools.product(range(L), repeat=n))
    for C, c in cnt.items():
        k = len(C)
        t = max(0, C[-1] + g - 1 - (L - 1))
        U = k * g - t
        pred = sum((-1) ** m * comb(k, m) * (U - m) ** n for m in range(k + 1))
        assert c == pred, (C, c, pred)
    # configurations of the same size k and the same truncation t are equiprobable
    groups = {}
    for C, c in cnt.items():
        groups.setdefault((len(C), max(0, C[-1] + g - 1 - (L - 1))), set()).add(c)
    assert all(len(v) == 1 for v in groups.values())
    assert any(t == 0 for (_, t) in groups) and any(t > 0 for (_, t) in groups)
