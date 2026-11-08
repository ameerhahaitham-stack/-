# Task 2 — null reference exchangeable with the production path: construction, proof, conditions, limits

## 1. What "exchangeable with production" has to mean
Production computes, for a template **T** (the strata pool of each of the k events, k itself, the eligibility rule, the gap g = 5, the retry/failure rule) and a fixed price series
**R** = (R_i)_i (R_i = forward move of bar i in ATR units),

  p = (1 + #{m : C_m ≥ obs}) / (1 + M),  obs = Σ_j R_{x_j}/k,  C_m = Σ_j R_{y^{(m)}_j}/k,

where the control configurations y^{(m)} are M draws of the production sampler S_T (random-order sequential placement, rejection of dead ends, ≤4M attempts).

**Lemma 1 (rank lemma).** If (obs, C_1..C_M) are exchangeable given (T, R), then P(p ≤ a | T, R) ≤ a for every a (equality for a ∈ {r/(M+1)} when there are no ties). Conversely, if the law of the observed configuration X given (T, R) is Q_T, p is super-uniform for every R **iff** the statistic's law under Q_T is stochastically dominated by that under S_T — in particular it is guaranteed when **Q_T = S_T**.
So everything reduces to one question: *what is the law of the observed event configuration given the template?*

## 2. Three references, and what each one proves
| reference | law of the observed configuration X given T | exchangeable with production? | what it proves |
|---|---|---|---|
| **R-S "matched null"** | X is one draw of the production sampler S_T itself | yes, by construction (X and the M controls are i.i.d. from S_T; the retry rule is the same) | the *machinery* (p formula, counting, failure handling, resolution) is calibrated: P(p≤a) = a. It says **nothing** about real events, which are not drawn from S_T. |
| **R-G "unconditional G"** (previous round, p_ref) | X ~ G (n iid bars, sort, greedy de-dup) | exchangeable with *G-draws*, **not** with S_T-draws | exact test against the G null; not production-matched (it ignores T) |
| **R-U "conditional-uniform"** (this round, Besag–Clifford chain, p_bc) | X ~ Uniform over all feasible configurations given T | **not** with S_T (S_T ≠ uniform, Lemma 3) but exchangeable with X under the uniform null | exact for any null whose conditional law is uniform-feasible; G is such a null (Lemma 2) |

## 3. Lemmas (all checked numerically in this repository)
**Lemma 2 (G given k is uniform over feasible configurations).** Let G draw n iid uniform bars on a domain of L bars, sort, and keep a bar iff it is ≥ g after the last kept bar. For a feasible configuration C = (c_1<…<c_k) (gaps ≥ g) every raw tuple that de-duplicates to C has all its bars in the "shadows" [c_j, c_j+g−1] and hits every c_j; shadows are disjoint, |U| = k·g − t(C) (t = truncation of the last shadow by the end of the domain, 0 unless c_k > L−g). Hence
  N(C) = Σ_{m=0..k} (−1)^m C(k,m) (|U|−m)^n,
which depends on C **only through k and t**. So P(C | k) is uniform over configurations with the same truncation, i.e. uniform over all feasible configurations except those whose last bar lies within g−1 bars of the domain end (tiny boundary effect). *Verified by exhaustive enumeration (tests/test_audit_theory.py) and numerically: close-pair counts of G|k and of the exact uniform sampler agree (23.78 vs 23.72 pairs ≤ 7 bars).*

**Lemma 3 (production's sequential sampler is not uniform).** S_T places events one after the other in a random order, each uniformly among the still-allowed bars (random sequential adsorption). A configuration's probability then depends on how many placement orders/available-bar sequences lead to it, which is *not* constant over feasible configurations: RSA favours spread-out configurations. *Measured: 22.1 vs 23.7 close pairs (≤7 bars) at k = 98 on 1490 bars (−7%).* Because Var(Σ R_x/k) increases with Σ_{i<j} Cov(R_{x_i},R_{x_j}) (= K(φ) = Σ φ^{|x_i−x_j|} under AR(1)), a control law with fewer close pairs has a smaller variance than the observed (uniform/G) configurations ⇒ the observed statistic is too dispersed relative to the controls ⇒ optimistic p-values in both tails (one-sided p: the upper tail).

**Lemma 4 (Besag–Clifford, exact reference by a reversible chain).** Let π_T be the uniform law over feasible assignments (slot j ↦ a bar of pool_j; all gaps ≥ g). The kernel "pick a slot uniformly, propose a bar uniformly from its pool, accept iff feasible" has a symmetric proposal, so it is reversible with stationary law π_T. Start from the observed configuration x₀. Draw J ~ U{0,…,M}; generate J thinned steps backward and M−J forward from x₀ (same kernel, by reversibility). If x₀ ~ π_T the M+1 states form a stationary chain whose index J of the observed state is uniform and independent of the chain, so the rank of the observed statistic among the M+1 states is uniform on {1,…,M+1} (ties give ≤). Therefore P(p_bc ≤ a) ≤ a **for any chain length, thinning or mixing speed** — mixing only affects power. Implemented in `src/quantlab/audit/bc.py` (numba); validity was additionally checked by simulation (section "p_bc" in the tail table).

## 4. Conditions under which each statement holds (the exchangeability conditions)
1. **Fixed price path.** R is fixed (or independent of the event draw): the null is "event timing carries no information about R given T". Events defined by rules on the past of R violate independence unless the rule is non-informative about the future; under a true edge-free market this is what the null states.
2. **Same template.** obs and the controls use the same strata pools, same k, same eligibility rule and same gap; any fallback pool (stratum < 5 bars) must be applied identically (here: `template_preserved` flag; share reported).
3. **Same support.** Controls must live on the support of the event process. In the synthetic G design the events never occur in the first 60 / last 50 bars while production controls use the whole eligible window; this *support mismatch* is a property of the synthetic design (real rules also need warm-up bars, so a milder version exists in real data).
4. **Same failure rule.** Dead ends are discarded identically for both sides; for R-S this is automatic, for R-U the chain never dead-ends (its moves are only accepted when feasible).
5. **Law of X given T.** p is exactly calibrated iff the real event process has the reference's law given T (R-S: S_T; R-U: uniform-feasible). **For real, rule-based events this is a modelling assumption that no simulation can verify**: the real law is unknown (clustering, regularity). We therefore *measure the sensitivity* to it (modes C = bursty, R = quasi-regular) instead of claiming a calibration for real events.

## 5. Conclusion for Task 2
* A reference that is **exchangeable with production by construction** exists only for events generated by production's own sampler (R-S). It validates the machinery, not the real-event test.
* A reference that is **exact under the natural "no timing information" null** exists and is implemented (R-U / p_bc). It is **not** production-matched, because production's sampler is not uniform (Lemma 3).
* **No reference can be proven exchangeable with real rule-based events** without a model of how the rule places events; we make **no calibration claim for real events**, only for the synthetic nulls listed and bounds on the sensitivity to event geometry.
