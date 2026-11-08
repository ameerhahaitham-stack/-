"""Supplementary audit: empty months, gap compression and unequal trade counts. SYNTHETIC ONLY.

Production (stats._clusters / cluster_bootstrap): clusters = calendar months that contain >= 1 trade, renumbered 0..a-1 (empty months and the gaps
between active months disappear); a clusters are drawn with replacement from default_rng(12345).integers(0,a,(5000,a)); statistic = pooled mean R per trade
(ratio of sums); centred null; p=(1+#(null>=obs))/(1+5000).

Here the same data (calendar axis of Kc months, month totals s_m and trade counts c_m, c_m = 0 for empty months) are tested with:
  prod     production rule: active months only, iid resampling              (a = number of active months)
  cal      same bootstrap, but over ALL Kc calendar months (empty months are clusters with s=c=0; random number of trades per resample)
  cbb_act  circular block bootstrap (block 3) on the COMPRESSED active-month axis
  cbb_cal  circular block bootstrap (block 3) on the calendar axis
  t_act    cluster t on active-month totals (linearised ratio), a-1 df
  kv_cal   Kiefer-Vogelsang fixed-b (Bartlett b=1) on the calendar axis (empty months contribute u=0, so gaps are respected), reference = iid N(0,1) at Kc
  im_cal   Ibragimov-Mueller: 4 contiguous blocks of Kc/4 calendar months, block ratio estimates, t with 3 df
Generator: month activity (iid Bernoulli(p_act) or 2-state Markov chain with persistence), counts (active months: 1+Poisson(lam-1) or overdispersed),
trade R = rr2 draws (+2 w.p. 1/3 else -1, mean 0) + month effect me_m (AR(1) over CALENDAR months, sd sig) added to every trade of that month.
Everything has E[R]=0 trade by trade."""
from __future__ import annotations

import numpy as np
from scipy.stats import t as tdist

from .bootalt import NB, mult_matrix, prod_mx, cbb_mx, kv_ref, _bartlett_W

GSC = {
    "G1_dense_equal":            dict(p_act=1.0, counts="equal", rho=0.0, sig=0.0),
    "G2_p0.7_poisson_iid":       dict(p_act=0.7, counts="poisson", rho=0.0, sig=0.5),
    "G3_p0.7_poisson_AR0.8":     dict(p_act=0.7, counts="poisson", rho=0.8, sig=0.5),
    "G4_p0.4_poisson_AR0.8":     dict(p_act=0.4, counts="poisson", rho=0.8, sig=0.5),
    "G5_p0.4_poisson_AR0.5":     dict(p_act=0.4, counts="poisson", rho=0.5, sig=0.5),
    "G6_dense_negbin_iid":       dict(p_act=1.0, counts="negbin", rho=0.0, sig=0.5),
    "G7_dense_negbin_AR0.8":     dict(p_act=1.0, counts="negbin", rho=0.8, sig=0.5),
    "G8_markov0.7_AR0.8":        dict(p_act=0.7, counts="poisson", rho=0.8, sig=0.5, markov=0.85),
    "G9_markov0.5_AR0.8":        dict(p_act=0.5, counts="poisson", rho=0.8, sig=0.5, markov=0.85),
    "G10_p0.4_noeffect_poisson": dict(p_act=0.4, counts="poisson", rho=0.0, sig=0.0),
}
LAM = 5.0


def gen(name: str, Kc: int, reps: int, rng):
    sc = GSC[name]
    if sc.get("markov"):
        # stationary activity prob p_act, persistence q on the previous state
        q, pa = sc["markov"], sc["p_act"]
        act = np.empty((reps, Kc), bool)
        act[:, 0] = rng.random(reps) < pa
        # P(act|act)=q ; P(act|inact)= pa(1-q)/(1-pa) keeps stationary prob pa
        p_ia = pa * (1 - q) / (1 - pa)
        u = rng.random((reps, Kc))
        for k in range(1, Kc):
            act[:, k] = np.where(act[:, k - 1], u[:, k] < q, u[:, k] < p_ia)
    else:
        act = rng.random((reps, Kc)) < sc["p_act"]
    if sc["counts"] == "equal":
        cnt = np.full((reps, Kc), int(LAM))
    elif sc["counts"] == "poisson":
        cnt = 1 + rng.poisson(LAM - 1, (reps, Kc))
    else:
        cnt = 1 + rng.poisson(rng.gamma(1.0, LAM - 1, (reps, Kc)))
    cnt = np.where(act, cnt, 0)
    wins = rng.binomial(cnt, 1 / 3)
    s = 3.0 * wins - cnt
    if sc["sig"]:
        e = rng.standard_normal((reps, Kc)); me = e.copy()
        if sc["rho"]:
            a = np.sqrt(1 - sc["rho"] ** 2)
            for k in range(1, Kc):
                me[:, k] = sc["rho"] * me[:, k - 1] + a * e[:, k]
        s = s + sc["sig"] * me * cnt
    return s, cnt.astype(float)


def _boot_p(Sg, Cg, Mx, obs):
    sb = Sg @ Mx.T
    cb = np.maximum(Cg @ Mx.T, 1.0)
    return (1 + (((sb / cb) - obs[:, None]) >= obs[:, None]).sum(1)) / (1 + NB)


def gap_pvals(s: np.ndarray, c: np.ndarray) -> dict:
    reps, Kc = s.shape
    N = c.sum(1)
    ok = (N > 0) & ((c > 0).sum(1) >= 3)
    obs = np.where(N > 0, s.sum(1) / np.maximum(N, 1), 0.0)
    out = {k: np.ones(reps) for k in ("prod", "cal", "cbb_act", "cbb_cal", "t_act", "kv_cal", "im_cal")}
    na = (c > 0).sum(1)
    # production + block bootstrap on the compressed axis: group by number of active months
    order = np.argsort(~(c > 0), axis=1, kind="stable")
    sc_ = np.take_along_axis(s, order, 1); cc_ = np.take_along_axis(c, order, 1)
    for a in np.unique(na[ok]):
        rows = np.where(ok & (na == a))[0]
        Mx = mult_matrix(np.random.default_rng(12345).integers(0, a, size=(NB, a)), a)
        out["prod"][rows] = _boot_p(sc_[rows, :a], cc_[rows, :a], Mx, obs[rows])
        out["cbb_act"][rows] = _boot_p(sc_[rows, :a], cc_[rows, :a], cbb_mx(a), obs[rows])
        # t on active months: linearised ratio
        u = sc_[rows, :a] - obs[rows, None] * cc_[rows, :a]
        se = np.sqrt(a / (a - 1) * (u ** 2).sum(1)) / N[rows]
        out["t_act"][rows] = tdist.sf(obs[rows] / np.maximum(se, 1e-12), a - 1)
    r = np.where(ok)[0]
    out["cal"][r] = _boot_p(s[r], c[r], prod_mx(Kc), obs[r])
    out["cbb_cal"][r] = _boot_p(s[r], c[r], cbb_mx(Kc), obs[r])
    u = s[r] - obs[r, None] * c[r]
    W = _bartlett_W(Kc)
    st = s[r].sum(1) / np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", u, W, u), 1e-300))
    ref = kv_ref(Kc)
    out["kv_cal"][r] = np.maximum(1 - np.searchsorted(ref, st, side="left") / len(ref), 0.5 / len(ref))
    b = Kc // 4
    sb_ = s[r][:, :4 * b].reshape(len(r), 4, b).sum(2); cb_ = c[r][:, :4 * b].reshape(len(r), 4, b).sum(2)
    good = (cb_ > 0).all(1)
    g = np.where(cb_ > 0, sb_ / np.maximum(cb_, 1), 0.0)
    tt = g.mean(1) / np.sqrt(np.maximum(g.var(1, ddof=1) / 4, 1e-300))
    pim = tdist.sf(tt, 3); pim[~good] = 1.0
    out["im_cal"][r] = pim
    out["_n_active"] = na.astype(float); out["_n_trades"] = N
    return out
