# QuantLab — Supplementary Statistical Audit (synthetic only)

Companion to `docs/STATISTICAL_AUDIT_2026-11.md` (the first audit report). Same constraints: **diagnosis and measurement only** — no production file touched,
no protocol / threshold / split / 82-family change, no DEV / VALID / HOLD, no market data, no experiment registry opened, no PR created or merged, no fix implemented.
Production code studied: PR #5 head `576fe515…` (files byte-identical, see `docs/audit/NO_TOUCH_LOG.md`, re-generated for this supplement).
All earlier results are kept; one invalid run of this supplement (an axis bug in my own generator) is kept in `docs/audit/raw/invalid_t8_axisbug/` and was repeated.

**Completed:** bootstrap K=24 vs 60 (13 scenarios × 10 methods, size 100 000 reps, power at 4 effect sizes); long-run-variance reliability; empty-month/gap study (10 scenarios × 2 calendar lengths × 7 methods); Holm/82-family decomposition (36 cells × 5000 families); gate-overlap study; event T1 at φ=0, 0.5; S-mode at φ=0, 0.5, 0.95; C-mode at φ=0 (extra); drift-regime study for the bootstrap × control gates (3 settings × 300 studies); trade-control resolution/gate analysis (code reading + first-audit simulations).
**Not completed / limited (stated, not hidden):** (i) tail levels ≤0.005 for event p remain unresolved at every φ (not pursued, as instructed); (ii) the K comparison uses K∈{24, 60} at a fixed 5 trades/month (the first audit's K-grid 6…120 is kept for intermediate K); (iii) power was simulated at μ ∈ {0.1, 0.2, 0.3, 0.5}R only; (iv) T10 has 300 studies per setting, so its tail rates rest on 4–19 events (CIs given); (v) T9 reproduces only the gates computable from an R series (no cost-scenario, neighbour or control gate); (vi) the drift study is one synthetic family (two-state drift + AR(0.3) + one stop/RR geometry); (vii) all dependence structures are synthetic — **no claim is made about the dependence of real strategies**, which cannot be measured without touching market data.
**Unfavourable/inconvenient results are all reported; one run of mine was invalid (axis bug) and is preserved separately.**

---

## 0. الإجابة المباشرة (Arabic summary)

**هل توجد طريقة يمكن إثبات أنها تضبط الخطأ الإحصائي عند حجم VALID الحالي (≈24 شهراً، ≈120 صفقة) وعند عتبة Holm ≈0.00125؟ لا.** ولا يمكن إثبات ذلك لأن:
1. **الصلاحية** تعتمد على حدّ أعلى للاعتماد الزمني بين الأشهر لا يمكن تقديره من 24 نقطة (مقدّرات التباين طويل الأجل تُقلّل التباين بنسبة 15–75% حتى عند K=60، وتبقى متقلبة CV≈0.3–0.85). كل الطرق الخمس التي اختُبرت (t، Newey–West، fixed-b، AR-ESS، block bootstrap) تتضخم تحت استمرار الأنظمة؛ الطريقة الوحيدة التي بقي حجمها ≤2.5× حتى في أقسى سيناريو هي اختبار Ibragimov–Müller بأربع كتل (4 كتل × 6 أشهر).
2. **القوة**: حتى «الأوراكل» (تباين معروف تماماً) يحتاج متوسط ≈0.5R لكل صفقة (K=24) أو ≈0.35R (K=60) ليبلغ قوة 80% عند 0.00125؛ واختبار IM بأربع كتل قوّته ≈0.09 عند 0.5R. أي أن بوابة Holm على 82 فرضية **لا تستطيع عملياً تأكيد حافة بحجم 0.1–0.3R حتى لو كانت حقيقية**، وفي المقابل الاختبار الحالي يمنح إيجابيات كاذبة (3× عند الاستقلال، 8–56× مع الاعتماد).
3. البوابات الأخرى في VALID (expectancy، PF، ex-top5، السنوات، DD) **لا تضيف حماية** بعد اجتياز بوابة Bootstrap: النسبة الشرطية لاجتيازها ≈1.00 (اختبار T9).
4. بوابة الضوابط (p_vs_control ≤ 0.10) خارج Holm؛ دقتها 1/501 كافية لعتبة 0.10 لكنها لا تكفي لأي استنتاج دون ≈0.002. اختبار T10 (استراتيجية «شراء دائماً» بتوقيت عشوائي أي بلا مهارة): تجتاز بوابة Bootstrap عند 0.00125 في 3.3–6.3% من العينات (27–51× الاسمي)؛ وبوابة الضوابط وحدها معايَرة (≈0.11 عند 0.10) لكنها **مترابطة** مع Bootstrap (ارتباط رتبي 0.53–0.83) فيبقى اجتياز البوابتين معاً 1.3–3.0% (≈10–24× الاسمي): بوابة الضوابط تقلل الخطر ولا تلغيه.

**التوصية: المختبر غير جاهز لـ DEV إحصائياً** (التفاصيل في القسم 8). لم أنفّذ أي إصلاح.

---

## 1. Settings, seeds, trial counts (what was run)

| id | purpose | generator | seeds | reps / studies | raw files |
|---|---|---|---|---|---|
| T6 | K=24 vs K=60 (K changed alone), 13 null scenarios, 10 p-value methods, power at μ=0.1/0.2/0.3/0.5 R | `audit/bootalt.py::gen_month_sums` (n=5 trades/month; trade R = rr2 (+2 w.p. 1/3 else −1, sd≈1.41) ± dependence) | SEED0=20261120, `default_rng([SEED0, scen, K, mu_i, chunk])`; production index matrix `default_rng(12345)`, block-bootstrap matrix `default_rng(777)`, fixed-b reference `[424242, K]` 10⁶ draws | size 100 000 per (scenario,K); power 20 000 per (scenario,K,μ) | `docs/audit/raw/t6/*.npz`, `t6_config.json`; tables `t6_size.csv`, `t6_power.csv`, `t6_lrv.csv`, `t6_mde80.csv` |
| T7 | empty months / gap compression / unequal counts | `audit/gaps.py` | 20261121 | 60 000 per (scenario,Kc) × 10 × 2 | `raw/t7/*.npz`, `t7_gaps_size.csv` |
| T8 | Holm / 82-family decomposition (within-strategy vs between-strategy vs common-idx) | `scripts/audit/t8_holm.py` | 20261122 | 5000 families × 36 cells (82 strategies, K=24) | `raw/t8/*.npz`, `t8_holm_decomposition.csv`, `t8_holm_check.json` |
| T9 | do the other VALID gates add protection after the bootstrap gate | `scripts/audit/t9_gates.py` | 20261123 | 60 000 × 6 scenarios | `t9_gates.csv` |
| T1 (φ=0, 0.5) | event-sampler ablation | `scripts/audit/t1_ablation.py` (unchanged) | as first audit | 1500 studies × 16 sampler configurations each | `raw/t1_phi0.csv`, `raw/t1_phi0.5.csv` |
| S-mode (φ=0, 0.5, 0.95) | production-sampler matched null | `scripts/audit/t3_tail.py --mode S` (unchanged) | DEFAULT_SEEDS["S"] | 8000 each (levels 0.10/0.05 on the first 3000); φ=0.8 from the first audit (20 000) | `raw/t3_S_phi*.csv` |
| T10 | drift-regime null for bootstrap gate × control gate | `audit/tradecal.py::drift_study` | series 2 100 000+k, signals 12 000 000+k, controls 16 000 000+k | 300 studies × 3 settings (D0 μ=0, D1 μ=0.3, D2 μ=0.6) | `raw/t10_D*.csv` |

Scenario definitions (all have E[R]=0 trade by trade): N1 iid normal; N2 iid rr2; T1/T2/T3 trade-level AR(1) 0.1/0.3/0.7 (latent Gaussian, rank-transformed to rr2); M1 iid month effect (sd 0.5 trade-sd units);
M2/M3/M4 month effect with AR(1) across months 0.5/0.8/0.8 (sd 0.5/0.5/0.25); V1/V3 iid log-volatility sd 0.5/1.0 per month; V2 persistent log-volatility (AR 0.8, sd 0.5); S1 win/loss streak regime (persistence 0.9).
Tiers (**my labelling for reporting only; real-market dependence is unknown before data are used**): A = benign (N1, N2, T1, M1, V1); B = moderate (T2, M2, M4, V2, V3, S1); C = severe (T3, M3).
Month effects/regimes at "AR 0.8" are those in the first audit (C3) that produced 50×; I do not claim they are typical of real strategies — only that nothing in the available evidence rules them out.

Statistic and test (production): mean net R per trade, clusters = months containing ≥1 trade, 5000 centred resamples from `default_rng(12345)`, `p=(1+#(null≥obs))/(1+5000)`.
`tests/test_audit_bootalt_equiv.py` shows the batched implementation equals `stats.cluster_bootstrap` bit-for-bit (integer-lattice and continuous R).

---

## 2. Monthly cluster bootstrap (priority 1)

### 2.1 K=24 against K=60 with only K changed (same generator, same return law, same test; trades per month fixed at 5, so trades 120 vs 300)

Production p, ratio = actual rejection rate / nominal at α=0.00125 (100 000 reps, exact 95 % CI):

| scenario | K=24 | K=60 |
|---|---|---|
| N1 iid normal | 2.96 [2.67, 3.28] | 1.60 [1.39, 1.84] |
| N2 iid rr2 | 1.38 [1.19, 1.61] | 0.81 [0.66, 0.98] |
| T1 trade-AR 0.1 | 1.68 [1.46, 1.92] | 0.91 [0.75, 1.10] |
| T2 trade-AR 0.3 | 1.85 [1.62, 2.10] | 1.25 [1.06, 1.46] |
| T3 trade-AR 0.7 | 8.59 [8.09, 9.12] | 6.06 [5.64, 6.51] |
| M1 iid month effect | 2.21 [1.96, 2.48] | 1.21 [1.02, 1.42] |
| M2 month AR 0.5 | 12.6 [12.0, 13.3] | 10.1 [9.5, 10.6] |
| M4 month AR 0.8 (sd 0.25) | 13.8 [13.2, 14.4] | 13.9 [13.2, 14.5] |
| M3 month AR 0.8 (sd 0.5) | 56.0 [54.8, 57.3] | 53.3 [52.1, 54.6] |
| S1 streaks 0.9 | 7.89 [7.41, 8.39] | 5.52 [5.12, 5.95] |
| V1 vol iid 0.5 | 1.02 [0.85, 1.21] | 0.47 [0.36, 0.61] |
| V2 vol AR 0.8 | 1.21 [1.02, 1.42] | 0.70 [0.56, 0.87] |
| V3 vol iid 1.0 | 0.37 [0.27, 0.49] | 0.13 [0.07, 0.21] |

(K=60 for T3–S1 is in `docs/audit/t6_size.csv`; at 0.05 the same pattern: boot 1.21→1.11 (N1), 4.19→4.14 (M3).)

### 2.2 Why independence improves with K and dependence does not

Write the statistic as t = m̄ / √V̂ where m̄ is the mean of the K month totals and V̂ the variance estimate implied by the resampling. The production bootstrap's implied variance is the plug-in
V̂ = (1/K²) Σ(s_m − s̄)² (exactly the iid estimator, divided by K instead of K−1) — verified: `docs/audit/t6_lrv.csv`, estimator "boot", mean ratio to the true variance 0.96–0.98 under independence.

* **Independent months:** two finite-K defects, both O(1/K): (i) the factor (K−1)/K, (ii) the sampling noise of V̂ and the skewness of month totals, which make the tail of m̄/√V̂ heavier than the normal tail the p-value implicitly assumes (a Student-type tail with K−1 d.f.). As K grows V̂ → Var(m̄) and the studentised statistic → N(0,1), so the ratio → 1 (observed: 2.96 → 1.60 → 0.99 for normal outcomes at K = 24, 60, 120 in the first audit).
* **Dependent months:** V̂ converges to the **wrong limit**. For any stationary dependence, Var(m̄) = (σ²/K)(1 + 2Σ_{l≥1}(1−l/K)ρ_l) while the iid resampling estimates σ²/K. The ratio (design effect) DE = 1 + 2Σρ_l is a property of the process and does **not** shrink with K (measured DE, first audit: iid 1.04, AR0.7 1.7–2.1, regime persistence 2.6→4.1, flat in K; here mean V̂/true: M3 0.25 at K=24 and 0.24 at K=60). A p-value computed with a variance too small by DE has a z-score inflated by √DE, so tail exceedance is multiplied by ≈ exp(z²(1−1/DE)/2)/√DE: at z=3.02 (α=0.00125) and DE=1.7 that is ≈5, DE=2.1 ≈7.5 (observed 8.6 for T3), DE=4.1 ≈15 (observed 50–56 for M3 — regime tails are heavier than normal, so the normal formula **under**states the damage). The lower the α, the larger the multiplication: at α=0.05 the same DE gives only 1.7–4 (table in §2.4).
* Consequently more months only help to the extent that dependence is absent; with persistent regimes K=24, 60 and 120 are equally bad (M3: 56 / 53 / 53; first audit K-grid up to 120). This is a property of **the inference**, not of the number of resamples: §2.7.

### 2.3 Separating the dependence types (production p, ratio at 0.00125, K=24 → K=60)

* **Trade-to-trade dependence** (T1/T2/T3): AR 0.1–0.3 → 1.7–1.9× (≈ the iid small-K inflation); AR 0.7 → 8.6× because month totals inherit autocorrelation across month boundaries (corr of adjacent month totals ≈0.29, DE≈1.7–2.1).
* **Month-level dependence** (M1 vs M2/M3/M4): iid month effects → 2.2× (heterogeneity alone is nearly harmless); persistence is what hurts: AR 0.5 → 12.6×, AR 0.8 → 56× (sd 0.5) or 13.8× (sd 0.25).
* **Regime persistence in win/loss streaks** (S1): 7.9× (5.5× at K=60).
* **Time-varying volatility** (V1–V3): **conservative** at the Holm level (0.37–1.2×) at K=24 — heavier-tailed month totals widen the bootstrap distribution — but the oracle z-test with the TRUE sd is anti-conservative in the same scenarios (1.9–5.4×), i.e. the production result is an accident of compensating errors, not calibration.

### 2.4 Production test against alternatives (diagnostic only; none adopted)

Methods (all on the same datasets; all one-sided): `boot` production; `t` t-test on month totals, K−1 d.f.; `nw3` Newey–West (Bartlett, lag 3) with K−1 d.f.; `kv` Kiefer–Vogelsang fixed-b (Bartlett kernel, bandwidth K) with
reference distribution simulated at the same K; `ar1` t with variance × (1+ρ̂)/(1−ρ̂), ρ̂ = clipped lag-1 autocorrelation; `imq4` Ibragimov–Müller: 4 contiguous blocks (6 months each at K=24, 15 at K=60), t with 3 d.f.;
`imb6`: blocks of 6 months (4 blocks at K=24 ≡ `imq4`, 10 at K=60); `imb3` blocks of 3 months; `cbb3` circular month-block bootstrap (block 3); `oracle` z-test with the true sd.

**Worst-case size by tier — maximum ratio actual/nominal over the scenarios of the tier [max exact-CI upper], α=0.00125, 100 000 reps per scenario:**

| K | tier | boot | t | nw3 | kv | ar1 | imq4 | imb3 | cbb3 | oracle |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 | A | 2.96 [3.28] | 0.99 [1.18] | 4.04 | 0.95 [1.14] | 0.70 | 1.00 [1.19] | 0.90 | 7.15 | 1.89 |
| 24 | B | 13.8 | 6.9 | 12.4 | 3.1 | 4.9 | 1.48 [1.71] | 3.2 | 20.7 | 5.4 |
| 24 | C | 56.0 | 38.4 | 32.6 | 9.5 | 23.7 | **2.50 [2.80]** | 10.5 | 52.1 | 2.1 |
| 60 | A | 1.60 [1.84] | 1.03 [1.23] | 2.13 | 0.94 [1.12] | 0.78 | 1.04 [1.23] | 0.92 | 2.59 | 1.47 |
| 60 | B | 13.9 | 11.0 | 9.9 | 2.7 | 7.4 | 1.25 [1.46] | 5.5 | 13.0 | 3.8 |
| 60 | C | 53.3 | 47.3 | 25.4 | 5.0 | 23.2 | 1.61 [1.85] | 19.0 | 34.5 | 1.4 |

At α = 0.05 (K=24): boot 1.21 / 2.44 / 4.19 (tiers A/B/C), t 0.99 / 2.19 / 3.92, kv 0.98 / 1.53 / 2.14, **imq4 1.00 / 1.42 / 1.93**, cbb3 1.51 / 2.55 / 3.80, oracle 1.04 / 1.05 / 1.18 (K=60: imq4 0.99 / 1.21 / 1.36).
(Full per-scenario tables: `docs/audit/t6_size.csv`; run `python scripts/audit/t6_analyze.py`.)

Reading:
* **Production bootstrap**: anti-conservative already at tier A (3× for normal outcomes at K=24), 14× tier B, 56× tier C. It is never the best of the methods tried in any tier.
* **t on month totals / Newey–West / AR-ESS**: fix the small-K iid problem (t: 0.99 at A) but not persistence (7–47× at B/C). Newey–West needs far more than 24 months (at K=24 lag-3 NW is *worse* than the production bootstrap even at tier A: 4.0× vs 3.0×).
* **Block bootstrap (cbb3)**: worst of all at K=24 (7–52×): with 8 blocks of 3 months the resampled series' sd is too small.
* **Fixed-b (kv)**: correct in tier A, mildly anti-conservative in B (≤3.1×), 9.5× in C at K=24 (5× at K=60); it is the best of the "ordinary" tests.
* **IM (4 blocks)**: the only procedure whose worst case stays ≤2.5× in the severe tier at K=24 and ≤1.6× at K=60 (1.2–1.5× in tier B). It has theory: Ibragimov & Müller (2010) prove size control for t-tests on q independent-in-the-limit group estimates for α ≤ ~0.08 under heterogeneous, weakly dependent data. It is only as good as the premise that 6-month blocks are approximately independent — false when regimes last longer than 6 months (tier C), which is where the 2.5× comes from.
* The oracle shows what an exactly known variance would give: ≈1 for everything except volatility mixtures — i.e. the missing ingredient is the variance (long-run variance) estimate, not the resampling mechanics.

### 2.5 Long-run-variance estimators when only 24 months are available (`docs/audit/t6_lrv.csv`)

Mean of V̂ / true Var(m̄), (coefficient of variation of V̂), P(V̂ < 0.5·true), K=24 → K=60:

| scenario | boot / t | nw3 | ar1 | imb6 (IM blocks) |
|---|---|---|---|---|
| N2 iid | 0.97 (0.27), 0.02 → 0.98 (0.17), 0.00 | 0.89 (0.48), 0.17 → 0.95 (0.30), 0.03 | 1.17 (0.38), 0.01 → 1.10 (0.23), 0.00 | 1.01 (0.81), 0.31 → 0.99 (0.47), 0.13 |
| T2 trade-AR 0.3 | 0.87 (0.26), 0.04 → 0.89 (0.16), 0.00 | 0.86 (0.48), 0.18 → 0.92 (0.30), 0.03 | 1.11 (0.42), 0.02 → 1.05 (0.27), 0.00 | 1.00 (0.81), 0.33 → 0.98 (0.46), 0.13 |
| M2 month AR 0.5 | 0.55 (0.30), 0.43 → 0.56 (0.19), 0.30 | 0.68 (0.54), 0.36 → 0.75 (0.34), 0.15 | 0.84 (0.58), 0.22 → 0.84 (0.38), 0.09 | 0.85 (0.82), 0.38 → 0.86 (0.47), 0.19 |
| M3 month AR 0.8 | 0.25 (0.32), 0.99 → 0.24 (0.21), 1.00 | 0.36 (0.61), 0.79 → 0.41 (0.40), 0.76 | 0.44 (0.74), 0.73 → 0.45 (0.51), 0.69 | 0.51 (0.85), 0.61 → 0.52 (0.51), 0.54 |

(boot and t are the same estimator up to the factor (K−1)/K. The Bartlett fixed-b estimator is deliberately biased (≈1/3 of the truth; its reference distribution compensates) so it is omitted here.)

Conclusion: **no estimator is reliable with 24 months.** Under independence the single-sample error of V̂ is already ±27–80 % (CV); with persistence every estimator is biased low (by 15 % to 75 %) **and** the bias does not shrink between K=24 and K=60; the more dependence-aware an estimator is, the noisier it is (CV 0.5–0.85). An analyst cannot know from the data in hand which regime applies.

### 2.6 Power (K=24 and 60; 20 000 reps per μ, exact CIs in `docs/audit/t6_power.csv`) and minimum detectable effect

Power at α=0.00125 for mean net R per trade μ (trade sd ≈1.41–1.6):

| scenario, K | μ | boot | t | kv | imq4 | oracle |
|---|---|---|---|---|---|---|
| N2, 24 | 0.1 / 0.2 / 0.3 / 0.5 | 0.014 / 0.067 / 0.224 / 0.766 | 0.007 / 0.036 / 0.143 / 0.689 | 0.007 / 0.027 / 0.079 / 0.338 | 0.004 / 0.012 / 0.026 / 0.086 | 0.015 / 0.077 / 0.240 / 0.809 |
| N2, 60 | 0.1 / 0.2 / 0.3 / 0.5 | 0.029 / 0.248 / 0.711 / 0.999 | 0.025 / 0.232 / 0.703 / 1.000 | 0.016 / 0.106 / 0.315 / 0.755 | 0.009 / 0.032 / 0.076 / 0.259 | 0.037 / 0.291 / 0.747 / 1.000 |
| T2 trade-AR, 24 | 0.1 / 0.2 / 0.3 / 0.5 | 0.012 / 0.047 / 0.133 / 0.556 | 0.006 / 0.024 / 0.082 / 0.458 | 0.004 / 0.014 / 0.042 / 0.196 | 0.003 / 0.008 / 0.017 / 0.053 | 0.008 / 0.037 / 0.116 / 0.524 |
| M3 regime, 24 | 0.1 / 0.2 / 0.3 / 0.5 | 0.124 / 0.203 / 0.302 / 0.542 (**size 56× nominal**) | 0.088 / 0.155 / 0.241 / 0.467 | 0.022 / 0.042 / 0.065 / 0.144 | 0.006 / 0.010 / 0.016 / 0.034 | 0.003 / 0.009 / 0.022 / 0.079 |

MDE at 80 % power, α=0.00125 (`docs/audit/t6_mde80.csv`): **≈0.50R per trade at K=24 (120 trades) even for the oracle** (N2), ≈0.35–0.36R at K=60 (300 trades) for boot/t/oracle, ≥0.5R for every method under tier B/C at K=24; IM 4-block: >0.5R (K=24) and >0.5R (K=60) — it cannot confirm an edge of that size.
At α=0.05 (no multiplicity) the MDE is ≈0.33–0.35R (K=24, N2), 0.21R (K=60). The VALID rule requires expectancy ≥0.10R: a strategy exactly at the protocol minimum (0.10R) has power ≈1–3 % at the Holm threshold with 120 trades.
The apparent power of the production test under persistence (M3: 12 % at μ=0.1R) is **size inflation**, not information (its size is 56× nominal).

### 2.7 More resamples are not a cure

From the first audit (kept): at B2/T3-type dependence the ratio at 0.00125 is 8.0 (1000 resamples), 8.72 (5000), 9.12 (20 000), 9.16 (100 000); regime C3: 52.7× vs 51.2×. The p-value converges to the bootstrap-distribution tail probability — which is the wrong distribution; more draws only make the wrong answer more precise (reducing decision noise: relative SD of p̂ at p*=0.00125 ≈ 40 % with 5000 draws, ≈ 9 % with 100 000). The t6 tables make the same point from the other side: oracle-variance z-tests need no resampling at all and are calibrated.

### 2.8 Verdict on the question "is there a method that provably controls the error at the VALID sample size?"

* **Not provable, and not achievable in the tested envelope.** With 24 monthly clusters (i) no variance estimator is reliable (§2.5), (ii) the only method whose worst-case size stays within ≈2.5× across all 13 scenarios is IM with 4 blocks, but it has essentially no power at α=0.00125 (≤9 % at 0.5R) and its size guarantee rests on an unverifiable independence premise for 6-month blocks, (iii) every method that has usable power (boot, t, nw, ar1, cbb) is anti-conservative as soon as month-level persistence exists (7–56× at the Holm threshold).
* What **is** established: under approximately independent months (tier A) the t-test on month totals (K−1 d.f.) and fixed-b do not exceed nominal by more than ≈20 % at 0.00125 (CI upper 1.14–1.18 at K=24; 1.12–1.23 at K=60; conservative in the volatility scenarios, 0.3–0.6×), while the production bootstrap is 3× at K=24 (normal outcomes) and ≈1.4–1.8× for skewed outcomes; at K=60 the production bootstrap becomes acceptable only for independent months (0.8–1.6×).
* What is **not** established (needs a decision/data): whether month-level persistence of a strategy's R is weak enough in real data to put us in tier A. That cannot be settled with synthetic data and is **not** to be settled with VALID/HOLD; options that do not touch VALID/HOLD are listed in §8.

### 2.9 The other VALID gates give no extra protection once the bootstrap gate passes (T9; K=24, 120 trades, 60 000 reps per scenario)

Gates reproduced from `criteria.valid` that can be computed from the R series: expectancy ≥0.10R, PF ≥1.2, expectancy ex-top-5 >0, positive-year share ≥0.5 (two calendar years), total/maxDD ≥1 and maxDD ≤20R.
P(boot p≤0.00125) [exact CI] and P(all of these gates | boot gate passed): N2 0.0017 [0.0014, 0.0021], conditional pass 1.000; T2 0.0023, 1.000; M4 0.0185, 1.000; S1 0.0097, 1.000; T3 0.0104, 0.973; M3 0.0690 [0.067, 0.071], 0.998.
A strategy that clears the bootstrap gate at p≤0.00125 has essentially always cleared the performance-threshold gates by construction (p≤0.00125 requires mean ≳3 SE ≫ 0.10R); they are **not** independent protection. (Cost-scenario, parameter-neighbour and control gates were not simulated here.)

---

## 3. Empty months, gap compression, unequal trade counts (T7)

**What the code does** (`stats._clusters`, `cluster_bootstrap`): clusters are the calendar months that contain ≥1 trade (`pd.factorize` of the month period), renumbered 0…a−1; `a` clusters are drawn with replacement; the statistic is the pooled mean R per trade (ratio of sums). So (i) empty months are not clusters, (ii) the gaps between active months vanish, (iii) cluster sizes (trades per month) are random and enter through the ratio.

**Design (`audit/gaps.py`)**: calendar window Kc ∈ {24, 60} months; activity: iid Bernoulli(p_act) or a 2-state Markov chain (clumped dormancy, persistence 0.85); trades per active month 1+Poisson(4) (or overdispersed negative-binomial mixture); trade R rr2 + month effect (AR(1) over **calendar** months, sd 0.5) — so correlation across a gap decays like ρ^gap and E[R]=0 trade by trade. 60 000 reps per cell.
Methods on the same data: `prod` (production rule); `cal` (same bootstrap but over all Kc calendar months, empty months = clusters with s=c=0); `cbb_act` / `cbb_cal` (block bootstrap on the compressed / calendar axis); `t_act` (cluster t, a−1 d.f.); `kv_cal` (fixed-b on the calendar axis, empty months contribute 0: gaps are respected); `im_cal` (4 calendar blocks).

Ratio actual/nominal at α=0.00125 (exact CIs in `docs/audit/t7_gaps_size.csv`), Kc=24 | Kc=60:

| scenario (mean active months, mean trades at Kc=24) | prod | cal | t_act | kv_cal | im_cal |
|---|---|---|---|---|---|
| G1 dense, equal counts, no month effect (24, 120) | 1.55 \| 0.88 | 1.55 \| 0.88 | 0.71 \| 0.71 | 0.65 \| 0.87 | 0.84 \| 0.72 |
| G10 p_act 0.4, Poisson counts, **no** dependence, no month effect (9.6, 48) | **8.85** \| 2.21 | 5.65 \| 1.81 | 1.00 \| 0.65 | 2.72 \| 1.25 | 0.75 \| 1.05 |
| G2 p_act 0.7, Poisson, iid month effect (16.8, 84) | 4.09 \| 1.77 | 3.48 \| 1.65 | 0.96 \| 0.88 | 1.19 \| 1.07 | 0.92 \| 0.80 |
| G6 dense, overdispersed counts, iid month effect (24, 120) | 5.12 \| 2.56 | 5.12 \| 2.56 | 1.77 \| 1.44 | 1.56 \| 1.29 | 1.05 \| 1.27 |
| G5 p_act 0.4, month AR 0.5 (9.6, 48) | 18.1 \| 6.2 | 12.3 \| 5.3 | 2.45 \| 2.45 | 4.93 \| 2.12 | 0.92 \| 0.88 |
| G3 p_act 0.7, month AR 0.8 (16.8, 84) | 41.8 \| 36.2 | 38.6 \| 35.0 | 20.9 \| 28.4 | 9.1 \| 4.7 | 2.05 \| 1.40 |
| G4 p_act 0.4, month AR 0.8 (9.6, 48) | 37.1 \| 21.2 | 27.0 \| 18.6 | 7.3 \| 12.2 | 9.5 \| 3.9 | 1.40 \| 1.01 |
| G7 dense, overdispersed counts, month AR 0.8 (24, 120) | 52.3 \| 47.5 | 52.3 \| 47.5 | 37.2 \| 41.3 | 10.2 \| 5.3 | 2.29 \| 1.52 |
| G8 Markov-clumped activity 0.7, AR 0.8 (16.8, 84) | 45.6 \| 38.2 | 41.8 \| 37.1 | 22.3 \| 30.8 | 11.0 \| 5.2 | 1.80 \| 1.56 |
| G9 Markov-clumped activity 0.5, AR 0.8 (12, 60) | 49.9 \| 35.8 | 42.2 \| 32.9 | 15.9 \| 24.8 | 23.1 \| 8.9 | 0.81 \| 0.96 |

Findings (each from the table; no assumption made beforehand about whether dropping empty months is right):
1. **Dropping empty months, by itself, is not the dominant defect.** Over the same data, resampling all calendar months (`cal`) is slightly less inflated than `prod` when many months are empty (G10: 8.85 → 5.65; G4: 37 → 27; G9: 50 → 42) and equal when none are empty (G1, G6, G7: identical). The ordering `prod` ≥ `cal` is consistent but the gain is modest compared with the effect of dependence (G3 41.8 vs 38.6).
2. **The number of active months is the first-order driver under independence.** G10 has *no* dependence of any kind and still gives 8.85× (9.6 active months, ≈48 trades): the production rule resamples `a` clusters, so a sparse strategy over 24 calendar months behaves like K≈10, not K=24 (compare the K-grid in the first audit: 10.9× at K=6, 3.3× at K=12). `n_clusters` (= number of active months) is already returned by production (`bs["n_clusters"]`) and stored in the trial summary.
3. **Unequal trade counts matter by themselves.** Dense calendar, iid month effect: equal counts (M1 in T6) 2.2×; Poisson counts at 84 trades 4.1× (G2); overdispersed counts 5.1× (G6). The pooled ratio estimator weights months by trade count, so the heavy months dominate the numerator while the resampling variance reflects a random denominator; this inflates the tail beyond the equal-count case at the same K.
4. **Compressing gaps does not change what the iid bootstrap ignores; it only hides how far apart clusters are.** With dependence across calendar months (ρ^gap), compression makes adjacent active clusters *less* dependent than they look in the index but the iid resampling ignores dependence in either case: G3/G4/G8/G9 are 21–52× on both `prod` and `cal`. A method that respects the calendar axis (`kv_cal`, `im_cal`) is clearly better than the same method applied after compression: `kv_cal` 9–23× (Kc=24), `im_cal` 0.8–2.3×, versus `t_act` (compressed) 7–37×.
5. **Correlation across a gap of several empty months** (G8/G9, clumped activity, AR 0.8 per calendar month): decays to ρ^gap; the cluster t on compressed months (`t_act`: 16–31×) treats the compressed neighbours as adjacent-and-weakly-dependent, the calendar-axis fixed-b (`kv_cal`) respects the gaps (11–23× at Kc=24, 5.2–8.9× at Kc=60) but remains anti-conservative; only the 4-block calendar IM test stays near nominal (0.8–1.8×) — with the power limitation of §2.6.
6. **Is the sampling unit / target quantity preserved?** The unit (calendar-month cluster of trades) and the target (pooled mean R per trade, ratio of sums) are preserved *conditional on the set of active months*. That conditioning is harmless if trading activity is independent of returns under H0. The audit shows the resulting inference is nonetheless invalid, but for the reasons in §2 (cross-month dependence, small effective K, unequal counts) rather than because empty months are dropped. What dropping does change is the effective K (a, not Kc), which is the most important number for sparse strategies.
7. **At Kc=60 (DEV length) the same patterns hold with smaller iid inflation** (G10 2.2×, G2 1.8×, G6 2.6×) and unchanged dependence inflation (21–48×).

No alternative method is proposed for adoption; the point is that the calendar axis, the number of active months and cluster-size heterogeneity are three additional reasons the nominal K=24 headline overstates the effective sample size.

---

## 4. Holm and the 82-hypothesis family (T8)

### 4.1 Why Holm is computationally right
`stats.holm` was compared with the first-step criterion over 1 200 stored families (`t8_holm_check.json`; 0 mismatches) and with an independent re-implementation in the first audit (0 mismatches /3000). Holm rejects *at least one* hypothesis iff min p ≤ α/m; therefore **the FWER of Holm is exactly P(min_i p_i ≤ 0.10/82)** — whatever the later steps do cannot change whether a family produces a false finding. With m=82 and α=0.10 the threshold is 0.00122.
Holm/Bonferroni guarantee FWER ≤ α **iff** each p_i is (super-)uniform under its own null (marginal validity). Dependence between hypotheses is allowed; **inflated individual p-values are not**: Holm's guarantee is conditional on its input being valid p-values. It was never designed to repair biased marginals.

### 4.2 Decomposition of the 0.589 (5000 families × 36 cells; 82 strategies, all null; K=24, 5 trades/month; exact CIs; `docs/audit/t8_holm_decomposition.csv`)

Factors: **A** within-strategy temporal dependence (none; trade-level AR 0.7 — the original 0.589 case; own month effect AR 0.5; own month effect AR 0.8); **B** between-strategy dependence ρ (shared trade noise *and* shared month effect: x_i = √ρ·x_common + √(1−ρ)·x_own); **C** one **common** index matrix (production: `default_rng(12345)`) vs **independent** 5000×K matrices per strategy; **D** production bootstrap p vs the oracle-variance z-test (exactly known sd).

| A within | ρ | FWER, boot, common idx [CI] | FWER, boot, independent idx | mean false rejections (boot) | per-test rate / nominal (boot) | 1−(1−q)^82 | oracle-variance FWER |
|---|---|---|---|---|---|---|---|
| none (iid rr2) | 0 | 0.146 [0.136, 0.156] | 0.147 [0.137, 0.157] | 0.157 | 1.57× | 0.145 | 0.123 |
| none | 0.5 | 0.102 [0.093, 0.110] | 0.100 [0.092, 0.109] | 0.167 | 1.67× | 0.154 | 0.087 |
| none | 0.9 | 0.039 [0.034, 0.045] | 0.040 [0.035, 0.046] | 0.153 | 1.53× | 0.142 | 0.032 |
| trade-AR 0.7 | **0** | **0.592 [0.578, 0.606]** | 0.592 [0.578, 0.606] | 0.887 | **8.87×** | **0.590** | 0.179 |
| trade-AR 0.7 | 0.5 | 0.261 [0.249, 0.274] | 0.262 [0.250, 0.274] | 0.884 | 8.84× | 0.589 | 0.086 |
| trade-AR 0.7 | 0.9 | 0.076 [0.069, 0.084] | 0.075 [0.068, 0.083] | 0.806 | 8.06× | 0.555 | 0.019 |
| own month AR 0.5 | 0 | 0.728 [0.715, 0.740] | 0.724 [0.712, 0.737] | 1.307 | 13.1× | 0.732 | 0.099 |
| own month AR 0.5 | 0.5 | 0.359 [0.346, 0.373] | 0.358 [0.345, 0.372] | 1.310 | 13.1× | 0.733 | 0.052 |
| own month AR 0.5 | 0.9 | 0.123 [0.114, 0.132] | 0.121 [0.112, 0.130] | 1.406 | 14.1× | 0.759 | 0.018 |
| own month AR 0.8 | 0 | **0.997 [0.996, 0.999]** | 0.998 [0.996, 0.999] | 5.69 | 56.9× | 0.997 | 0.093 |
| own month AR 0.8 | 0.5 | 0.656 [0.643, 0.670] | 0.655 [0.641, 0.668] | 5.68 | 56.8× | 0.997 | 0.048 |
| own month AR 0.8 | 0.9 | 0.280 [0.267, 0.293] | 0.281 [0.269, 0.294] | 5.67 | 56.7× | 0.997 | 0.011 |

Answers to the four separations:
1. **Dependence in time inside each strategy** is the whole story of the 0.589: for independent strategies FWER = 1−(1−q)^82 with q = the *per-test* false-rejection rate at the nominal 0.10/82; here q is 8.87× the nominal (0.0108 vs 0.00122) so 1−(1−q)^82 = 0.590 ≈ 0.592 observed. Replace the bootstrap p by a p with correct marginal validity (oracle variance) and the same data give 0.09–0.18 (0.179 for trade-AR 0.7 — the oracle z is itself not exact for skewed rr2 sums at this tail — and 0.093–0.099 for month-effect AR cases).
2. **Dependence between strategies (ρ)** does not change the per-test false rate (ratio stays 8–57×) but **reduces the FWER** (0.592 → 0.261 → 0.076 as ρ goes 0 → 0.5 → 0.9) by *clumping* the same expected number of false rejections into fewer families (variance/mean of the number of raw rejections rises from ≈1 at ρ=0 to 12–43 at ρ=0.9). The expected number of false findings per family is unchanged (≈0.8–5.7). So between-strategy dependence is not a safety mechanism: it only makes false findings arrive together.
3. **The common index matrix** (`common_idx`, as in production) versus independent matrices: no measurable difference in any of the 12 comparisons (maximum |ΔFWER| = 0.004, all well within Monte-Carlo error; per-test rates identical to 3 digits). With 5000 resamples the resampling noise itself is nearly uncorrelated across strategies; for *independent* strategies the common matrix does not create dependence between p-values (variance/mean of the number of raw rejections at ρ=0 is 0.90–1.01, i.e. Binomial-like). The shared matrix is therefore not an additional source of inflation in these settings; its effect is not detectable at 5000 families per cell.
4. **Independent matrices per strategy** give the same FWER as the shared one, i.e. they would not repair anything.

### 4.3 Why Holm is correct but cannot guarantee FWER here
Holm controls FWER by construction **only if** P(p_i ≤ t) ≤ t for every true null i and every t. The production p violates this at small t by a factor R(t) (=8.9–57× at t=0.00122 in the persistent cases). Then FWER ≈ 1−(1−R·t)^m regardless of the correction chosen: the correction multiplies the threshold by 1/m but the marginal error was multiplied by R. Holm's step-down is a deterministic function of the p-values: given inflated inputs it faithfully returns inflated errors (checked: Holm vs first-step criterion, 0 mismatches). Blaming Holm for the 0.589 would be wrong — the table shows the same Holm gives 0.09–0.18 on valid-marginal p-values from the same data.

### 4.4 Relevance to the protocol's actual use
In the registry, the family contains **both** event-study trials (p_raw = event-study p) and strategy trials (p_raw = bootstrap p), m up to 82; the Holm-adjusted p of a VALID strategy is, in practice, ≈ 82 × its own bootstrap p (other trials have large p), so the VALID gate is effectively "bootstrap p ≤ ≈0.00122" — i.e. exactly the tail where §2 shows the inflation. The previously reported staged selection (DEV screen then VALID on fresh data) lowers the number of strategies that reach VALID (first audit: FWER 0.058 iid / 0.185 regime-persistence) but does not repair the marginal p.

---
## 5. Event comparison (event-study p) — gaps closed

### 5.1 Runs added (all synthetic; unchanged runners; seeds as in the first audit)
* T1 ablation at **φ=0** (1500 studies × 16 configurations) and **φ=0.5** (1500): PROD excess z-variance vs the exact G reference **+0.004 (SE 0.010)** at φ=0 and **+0.010 (SE 0.011)** at φ=0.5 — no detectable sampler-geometry effect (it was +0.020 (0.006) at φ=0.8 and +0.044 (0.009) at φ=0.95 on matched support). The no-gap controls (`indep`, `strata_only`) are over-conservative at every φ (sd ratio 1.22–1.27; ratio at 0.05 = 0.44 → 0.31); the order variants (time / reverse / per-draw), retry budget and strata variants change nothing (all within ±0.015 of PROD).
* **S-mode** (observed config drawn by the production sampler itself; only possible violation = the machinery): φ=0 (8000 studies), φ=0.5 (8000), φ=0.95 (8000), joined to the existing φ=0.8 (20 000).
* **C-mode φ=0** (clustered events; 3000 studies — added because the first audit had clustered events only at φ=0.8).

### 5.2 Event screen at the 0.10 threshold — production p, exceedance ratio actual/nominal [exact 95 % CI] (levels 0.10 / 0.05 use the first 3000 studies unless stated; level 0.01 all studies)

| event generator | φ | @0.10 | @0.05 | @0.01 |
|---|---|---|---|---|
| **S** (machinery only) | 0 | 1.03 [0.92, 1.14] | 1.04 [0.89, 1.21] | 1.03 [0.82, 1.27] |
| S | 0.5 | 1.05 [0.95, 1.17] | 0.99 [0.84, 1.16] | 1.00 [0.79, 1.24] |
| S | 0.8 | 1.02 [0.94, 1.11] (5000) | 1.04 [0.92, 1.17] | 0.92 [0.79, 1.06] |
| S | 0.95 | 0.92 [0.82, 1.03] | 0.95 [0.81, 1.12] | 0.93 [0.73, 1.16] |
| W (support-matched uniform events) | 0.8 / 0.95 | 0.92 [0.82, 1.03] / 1.00 [0.89, 1.11] | 0.97 / 1.05 | 0.88 / 1.05 |
| G (support-mismatched uniform events, as in round 4) | 0 / 0.5 | 1.00 [0.90, 1.11] / 0.93 [0.83, 1.04] | 0.91 / 1.01 | 0.97 / 1.05 |
| G | 0.8 / 0.95 | 1.04 [1.00, 1.09] / 1.12 [1.04, 1.20] | 1.08 / 1.18 | 1.16 [1.01, 1.31] / 1.37 [1.09, 1.69] |
| **C** (clustered timing) | 0.8 | **1.39 [1.24, 1.54]** (2000) | 1.60 [1.37, 1.86] | 2.32 [1.95, 2.73] |
| C | 0 | 0.94 [0.84, 1.05] | 0.97 [0.82, 1.14] | n/a (3000 studies, level not evaluated) | | |
| **R** (regular spacing) | 0.8 | 0.61 [0.51, 0.72] | 0.50 | 0.25 |

Conclusions on the 0.10 screen:
1. **Generator validity** (is the machinery right when the timing law is the one it assumes?): **yes at every φ tested** — S and W: all CIs contain 1 at 0.10/0.05/0.01 (ratios 0.92–1.05). The previous "optimism" at φ≥0.8 (G-mode: 1.04–1.37) is the support-mismatch artefact of the round-4 design plus a ≤+0.04 z-variance sampler-geometry residual that vanishes at φ≤0.5.
2. **Clustered timing is harmful only together with serial correlation:** C-mode at φ=0 is calibrated (0.94 [0.84, 1.05] at 0.10; shift reference 0.97) while at φ=0.8 it is 1.39× — the inflation is an interaction (event clustering × autocorrelation of the statistic), not a property of clustering alone. So the problem is wider than one φ but is not universal across null models.
3. **Timing-law validity** (is the null "events are placed like gap-constrained uniform draws" the right null for real rule-based events?): **not established, and not establishable from synthetic data.** If real events cluster (volatility bursts, trend continuation) the screen at 0.10 rejects ≈1.4× too often, at 0.01 ≈2.3×; if they are more regular than uniform it is conservative (0.5–0.6×). Both directions occur within a single plausible family of timing laws; the circular-shift reference stayed within 0.6–1.2 of nominal in all of them (including 1.04 / 0.99 / 0.90 at 0.10 / 0.05 / 0.01 for C).
4. The screen only grants "permission to freeze" in the protocol, but event-study p-values are **also trials in the Holm family** (p_raw = event p). Their level-0.10 use is acceptable within ±10 % under matched timing; their contribution at the tail (≈0.001–0.005) has not been resolved at any φ (expected ≤20 events at 0.001 with the available N; MDR80 ≈2×) and the tail resolution was deliberately not pursued as instructed.

### 5.3 Conditions for Besag–Clifford (R-U) — mathematical and practical
*Target law.* Fix the template T = (k, minimum gap g, eligible index set E ⊂ ℤ) and the series. Let 𝒞(T) be the set of g-separated k-subsets of E. The reference π is uniform on 𝒞(T) (that is what "G given k" is, up to the last-shadow boundary effect of Lemma 2; `docs/audit/EXCHANGEABILITY.md`).
*Validity theorem (Besag & Clifford 1989).* Let P be a Markov kernel on 𝒞(T) that is **reversible with respect to π** (here: Metropolis moves — move one event to a feasible position / swap — accepted w.p. min(1,1)=1 since π is uniform; irreducibility is *not* required for validity). Draw a random index J ∈ {0..M}, run the chain M−J steps *forward* and J steps *backward* from the observed configuration X₀ (backward = forward by reversibility); the M+1 configurations are exchangeable with X₀ **if X₀ ~ π under H₀**, so p = (1+#{statistic ≥ observed})/(1+M) is exactly super-uniform for **any** mixing speed (poor mixing costs power, never validity).
*Conditions that must hold in practice:*
1. H₀ must be "X₀ ~ π": the real events' timing is a uniform draw from 𝒞(T) *independent of the outcome statistic*. This is the **timing-law assumption** — the C and R modes show it can fail in either direction (C: p_bc 1.34 / 1.60 / 2.23 at 0.10 / 0.05 / 0.01 [same as p_prod]; R: 0.54 / 0.48 / 0.17).
2. T (k, g, E, the strata) must be determined without looking at outcomes; the chain must preserve k and the gap rule exactly and use the same eligible set for observed and chain states.
3. The same statistic function is applied to the observed and the chain states, on the same series.
4. Reversibility must be checked for the actual implementation (symmetric proposal; `bc.py` uses symmetric single-event moves with rejection of infeasible proposals — this keeps π uniform). The numba implementation is audit-only (optional dependency).
5. Practical: M ≈ 5000–20 000 with the lag-1 autocorrelation of the statistic along the chain ≈0.19 at thinning 2000 (measured) so effective M is ≈0.7M.
Besag–Clifford and the production p agree whenever the timing law matches (S/W modes, paired ratios 1.0–1.1) and **both** fail identically for clustered timing: the problem under C is the null model, not the sampler.

---

## 6. Trade-control comparison (separate from event-screen p and monthly-bootstrap p)

### 6.1 What the protocol actually does with the control p (read from `report.py`, `registry.py`, `experiment.py`, `protocol_params.json`; read-only)
* `matched_control(...)` (500 reps) produces `p_vs_control = (1+#{control mean ≥ signal mean})/(1+500)` for each strategy trial at VALID (and DEV).
* **It is not part of the Holm family.** `registry.family_table` uses `p_raw` only (= event-study p for event trials, = monthly-bootstrap p for strategy trials). The control p is a **separate mandatory VALID gate**: `beats_random_control: p_vs_control ≤ max_p_vs_control = 0.10`, an AND with the Holm-adjusted bootstrap gate and the other criteria, with **no multiplicity adjustment** (it is evaluated once per candidate, not over 82).
* Therefore three distinct p-values exist and must not be mixed: event-screen p (trial in the family; DEV screen at 0.10), monthly-bootstrap p (family; VALID gate via Holm ≈ p ≤ 0.00122), trade-control p (stand-alone gate at 0.10).

### 6.2 Resolution 1/501 and sufficiency for the gate
* The attainable values are j/501, j=1…501; step 0.002. At the gate (0.10) the requirement p ≤ 0.10 ⇔ at most 49 of 500 controls ≥ the real mean — the grid is 50× finer than the threshold, so **resolution is adequate for a 0.10 gate**.
* Monte-Carlo noise of p̂ at the gate: SD ≈ √(0.1·0.9/500) = 0.0134 (13 % of the threshold). The randomisation p with finite M is *exactly* super-uniform (not approximately) when controls are exchangeable with the observed history, so the noise costs reproducibility of borderline decisions (a true p of 0.12 passes with probability ≈ 8 %), not size. Fixed seeds make the decision deterministic, but not stable to a different seed.
* **It is not adequate for any inference below ≈0.002** and cannot serve as a Holm input: with m=82 the Bonferroni-equivalent target 0.0012 is below the smallest p (1/501=0.0020). The protocol does not use it that way.

### 6.3 Calibration summary (first audit, 800 studies per setting; exact CIs) and what the null does and does not cover
Null: random-timing signals, **random sides**, fixed stop in ATR / RR / max-hold; φ∈{0, 0.8, 0.95}; sparse/mid/crowded and a regular-signal stress case. P(p_vs_control ≤ 0.10) / nominal = 0.69–1.05 (upper CI bounds ≤1.43); at 0.05 0.65–1.05; control/reference sd ratio ≈0.985; executed controls 1.2–1.5× the real trades in the normal settings; **without** the subsample to n_real the test is anti-conservative at 0.10 (point ratios 1.16–1.60; sparse worst). The effect of non-overlap/redraw: the engine's concurrency rule thins controls exactly as it thins real trades (same engine), so executed counts differ (controls 1.2–1.5×, fewer in the regular stress case: 96 % of reps) and the random subsample restores equal n; where fewer controls than real trades execute, the test becomes conservative (0.70). Matching: side, stop distance (ATR units), RR, max-hold and the year×slot×volatility stratum are matched by construction; mean control hold ≈ real hold (ratio ≈1.0).

**Limits** (because the null is random-timing / random-side): it shows the control test is a valid randomisation *when the strategy's entry timing carries no information and sides are exchangeable*. It does not show validity (a) when the side is fixed and the market drifts (T10 below), (b) when entry timing is correlated with the volatility/stratum labels in ways the controls' strata do not capture, (c) for stop/RR/max-hold laws other than the three tested, (d) for tail inference.

### 6.4 Drift-regime null: fixed-side strategy with no timing skill (T10) — the combination of gates
Synthetic series (AR(0.3) returns plus a zero-mean persistent two-state drift ±μ per bar, regime persistence 0.995 per H4 bar ≈ 33 days; 4320 bars ≈ 24 months, ≈120 trades, 24 monthly clusters); signals = random timing, **always long**, stop 1.5 ATR, RR 2, max-hold 20; the strategy has no timing skill, but whichever regime lasted longer pays it (or costs it). Control = production `matched_control` (500 reps); bootstrap = production `cluster_bootstrap` (5000, seed 12345) on the same trades.
| setting | studies | mean R of the no-skill strategy | P(boot p ≤ 0.10) ratio [CI] | P(boot p ≤ 0.00125) [count] ratio [CI] | P(ctrl p ≤ 0.10) ratio [CI] | P(boot ≤ 0.00125 **and** ctrl ≤ 0.10) [count] | P(ctrl ≤ 0.10 \| boot ≤ 0.00125) | Spearman corr(p_boot, p_ctrl) |
|---|---|---|---|---|---|---|---|---|
| D0 (μ=0, no drift) | 300 | +0.111R | 3.07 [2.55, 3.62] | 0.0333 [10] 26.7× [12.9, 48.4] | 1.10 [0.77, 1.51] | 0.030 [9] (24×) | 0.90 | 0.83 |
| D1 (μ=0.3) | 300 | +0.115R | 3.43 [2.90, 4.00] | 0.0367 [11] 29.3× [14.8, 51.7] | 1.17 [0.83, 1.59] | 0.023 [7] (19×) | 0.64 | 0.67 |
| D2 (μ=0.6) | 300 | +0.156R | 4.13 [3.57, 4.71] | 0.0633 [19] 50.7× [30.9, 77.7] | 1.10 [0.77, 1.51] | 0.013 [4] (11×) | 0.21 | 0.53 |

(`docs/audit/t10_drift_summary.csv`; counts in brackets; the joint rate for the pair of gates is compared with the 0.00125 that the bootstrap gate alone is meant to deliver.)

Reading — **with a conceptual caveat that matters**:
* The always-long random-timing strategy is *not* an E[R]=0 strategy in these synthetic markets: even with zero drift (D0) its expectancy is **+0.11R** (AR(0.3) momentum + the stop/target geometry; SE of the mean 0.008). The bootstrap tests "E[R] ≤ 0" and correctly sees positive expectancy; it does not test "no timing skill". D0–D2 therefore do **not** measure the bootstrap's Type-I error (that is §2–§4); they measure what the VALID gates do with a strategy that has **no timing skill but a positive market-baseline expectancy** (market beta, drift regimes, barrier geometry) — the situation a matched control exists to detect.
* The matched control behaves as a valid randomisation in this setting: P(p_ctrl ≤ 0.10) ≈ 0.11 in all three settings, CIs contain 1 (also at 0.05, 0.01 within their wide CIs), even though the real mean is positive and the drift is persistent — because controls share the side, stops and the same market path.
* **But the control gate is not an independent second line of defence for the same false findings:** p_ctrl and p_boot are positively dependent (Spearman 0.53–0.83); among strategies that clear the bootstrap gate at 0.00125 between 21 % and 90 % also clear the control gate. The joint false-pass probability of the two gates for a no-skill strategy is 1.3–3.0 % per strategy over 24 months (counts 4–9 of 300; wide CIs), i.e. an order of magnitude above 0.00125, and it applies per strategy before any multiplicity across the 82-family. (In D2, where the drift is strongest, the control gate removes ≈80 % of the bootstrap passes; in D0 almost none.)
* Limits: 300 studies/setting (tail counts 4–19), one synthetic family; the numbers show the *direction and rough size*, not calibrated rates.


---
## 7. What can and cannot be relied on

| item | can be relied on | cannot be relied on |
|---|---|---|
| `stats.holm` / `registry.family_table` | arithmetic and step-down logic (0 mismatches in 4200 checks); FWER ≤ α with valid marginal p-values (oracle-variance cells: 0.011–0.179 overall; ≈0.09–0.18 at ρ=0, lower at ρ≥0.5 — the highest cell, trade-level AR(0.7), 0.179, is above 0.10 even for a z-test with the true sd — month totals are not normal at 5 trades/month; I did not isolate the cause) | any FWER statement when the inputs are production bootstrap p-values (0.04–0.998 depending on dependence; 0.146 even with no dependence at all) |
| monthly cluster bootstrap p (strategy) | iid-month case at K≥60 within ≈2× (N2 0.81, N1 1.6); ordering of strategies by evidence | tail p-values (≤0.01) at K=24 in any scenario (1.4–56×); anything under month-level persistence (7–56×, no improvement with K); the VALID gate at ≈0.00122 as a Type-I-error-controlled test; sparse strategies (effective K ≈ number of active months: G10 8.9×) |
| alternatives tested | t-test / fixed-b are near nominal when months are ≈independent (tier A); IM(4 blocks) has the best worst case (≤2.5×) | any alternative as a *proven* fix: all fail or lose power in some tier; none has usable power at α=0.00125 and K=24 for edges ≤0.3R |
| long-run variance from 24 months | order of magnitude only | any variance-correction factor estimated from the 24 VALID months (CV 0.3–0.85; biased low 15–75 % under persistence) |
| event-study p (generator) | calibrated to ±~10–25 % at 0.10–0.01 when timing law is the assumed one (S, W; φ=0–0.95); shift reference calibrated in every timing model tested | validity for real events (needs a justified timing model); anything at p < 0.005 (unresolved); optimism claims of round 4 (largely a design artefact) |
| trade-control p | valid randomisation under random-timing and drift/fixed-side nulls at the 0.10 gate (0.69–1.17 ratio); resolution 1/501 adequate for a 0.10 gate | any use below ≈0.002 or inside Holm; independence from the bootstrap gate (corr 0.5–0.8); nulls with timing–stratum dependence or other stop/RR laws (untested) |
| other VALID gates (expectancy, PF, ex-top5, years, DD) | meaningful for economic relevance | as protection against false positives once the bootstrap gate has passed (conditional pass ≈1.00) |

Unresolved / conflicting items and how I read them:
1. *Production bootstrap conservative (0.1–0.4×) under volatility mixtures while the oracle z is anti-conservative (1.9–5.4×).* Compensating errors (heavy-tailed month totals widen the resampled distribution); neither is calibrated; not evidence of safety.
2. *Round-4 G-mode excess vs matched S/W calibration.* Support-mismatch artefact + small geometry effect (+0.004/0.010 at φ=0/0.5, +0.02/0.044 at φ=0.8/0.95); the production machinery is not the issue, the null model for real events is.
3. *T10 D0 shows "inflation" at zero drift.* Not a Type-I failure (E[R]=+0.11R for a no-skill always-long strategy in this engine); read as above.
4. *First audit "0.589" was not reproduced at first in this supplement:* the first run of T8 generated the temporal dependence along the wrong axis (my bug, preserved in `docs/audit/raw/invalid_t8_axisbug/`); after the fix 0.592 [0.578, 0.606] reproduces it exactly.

---

## 8. Readiness for DEV — explicit recommendation

**The laboratory is not statistically ready for DEV (my recommendation; the decision is yours and the independent reviewer's).** Software tests passing is not the criterion; the inference is. Blocking conditions, each with measured size:

1. **The VALID significance gate is not a controlled test.** Monthly-bootstrap p at the Holm-equivalent threshold has 1.4–3× inflation under independence at K=24 and 7–56× under month-level persistence; no tested replacement is both controlled and powered at 24 months (§2.8). Family FWER with these p (82 null strategies, nominal 0.10) is 0.146 with no within-strategy dependence and independent strategies, 0.59–0.998 with within-strategy dependence (independent strategies); strong between-strategy dependence lowers the FWER (to 0.04–0.28 at ρ=0.9) only by clumping the same expected number of false rejections into fewer families (§4).
2. **The VALID design cannot confirm realistic edges at the Holm threshold.** MDE80 ≈0.5R/trade at K=24 even with a known variance (≈0.35R at K=60); the protocol minimum 0.10R has 1–3 % power. A VALID "pass" is mostly a large-effect or a false-positive event; a VALID "fail" says little about modest true edges.
3. **Dependence cannot be bounded from the data in hand.** Variance estimators from 24 months are biased and noisy; the key unknown (month-level persistence of strategy R) cannot be measured on VALID/HOLD without destroying their independence, and not at all with synthetic data.
4. **The event-study null assumes a timing law not justified for real rule-based events** (§5): 1.4–2.3× at 0.10–0.01 when clustering meets autocorrelation, 0.5× when regular; event p-values are also trials in the Holm family.
5. **The control gate does not rescue (1):** it is calibrated at 0.10 but dependent on the bootstrap gate; no-skill strategies with positive baseline expectancy pass both gates 1.3–3.0 % of the time per strategy (§6.4).
6. **Sparse strategies are worse than the K=24 headline** (effective K = active months; 8.9× with 9.6 active months, no dependence at all) and unequal trade counts add inflation (4–5×) (§3).

*What would have to be true to call the lab ready (conditions, not implementation):* (a) a decision on the strategy-level evidence standard that is shown by simulation to control Type-I error under the dependence envelope you accept (and a stated lower bound for the effect it can confirm); (b) a documented, approved way to estimate month-level dependence **without** VALID/HOLD; (c) a decision whether event-study p-values remain family members; (d) re-run of this audit's panel on the amended procedure, with CIs, before DEV.

**Separate recommendations per problem (statistical alternatives, pros/cons; nothing implemented):**

| problem | option | pros | cons |
|---|---|---|---|
| B. monthly bootstrap p | (i) keep as a descriptive/ranking statistic only, not as a significance gate | no new test; honest labelling | VALID then has no controlled significance gate |
| | (ii) month-total t-test (K−1 d.f.) | controlled when months ≈ independent (tier A: ≈nominal at 0.00125, K=24) | 6–47× under persistence (K=24→60); no dependence estimate |
| | (iii) fixed-b / Kiefer–Vogelsang | best of the standard tests (≤3.1× tier B, 9.5× tier C at K=24; 5× at K=60) | still anti-conservative under persistence; reference table by simulation |
| | (iv) Ibragimov–Müller 4 blocks (or q blocks) | has a size theorem; worst case ≤2.5× (K=24), ≤1.6× (K=60) | power ≈0 at 0.00125 (≤9 % at 0.5R); premise "blocks independent" unverifiable at 24 months |
| | (v) randomisation against the matched-control population as the *primary* test, with regime/block-preserving resampling | conditions on the same market path (handles drift/beta); tests the right null (timing skill) | needs calibration for nulls beyond random timing; resolution/cost of many controls; dependence on strata matching |
| | (vi) longer evidence windows / pooling (K≥60) | removes the iid small-K part (0.81–1.6×) | does nothing for persistence (53×); protocol windows locked |
| | (vii) more resamples | lowers decision noise (≈40 % → ≈9 % relative SD at p=0.00125) | does not change the bias (§2.7) |
| D. 82-family / Holm | keep Holm, fix the marginals first | Holm is correct; dependence between strategies reduces FWER | with current p, FWER 0.10–0.997 |
| | alternative multiplicity (e.g. effective number of tests, permutation max-T) | uses the dependence structure | requires valid marginals and an estimate of dependence; more assumptions |
| A. event p | restrict to a screen (permission to freeze) and remove from the Holm family, or keep with timing-robust reference (circular shift) | shift reference calibrated in all models tested | resolution 1/1581; a decision about family size (protocol parameter) is yours |
| | Besag–Clifford (exact for any mixing) | exact under uniform timing | same uniform-timing assumption (fails identically for clustered events) |
| C. trade-control | keep as a 0.10 gate, do not use in Holm/tails; increase reps (≥2000) if borderline reproducibility matters | calibrated; resolution adequate for 0.10 | dependent on bootstrap gate; limited nulls tested |
| | add drift/fixed-side and strata-dependent nulls to its calibration | closes the stated limit | more compute |
| Process | explicit "UNPROVEN / exploratory" label for any VALID pass until the above is decided | prevents false confidence | slower decisions |

---

## 9. Reproducibility, files, integrity

* Environment/commands/seeds: §1; additional commands: `python scripts/audit/t6_alt.py --K 24 60` (resumable), `t6_analyze.py`, `t7_gaps.py --reps 60000`, `t8_holm.py --fams 5000`, `t9_gates.py`, `t10_drift.py --setting {D0,D1,D2} --n 300`, `t10_analyze.py`, `run_queue6/7/8.sh` (event runs), then `t3_analyze.py`, `t1_analyze.py <csv>`, `build_tables.py`, `no_touch_proof.py`. Tests: `pytest tests/test_audit_*.py` (now includes `test_audit_bootalt_equiv.py`).
* Raw data: `docs/audit/raw/{t7,t8}/*.npz` (p-value arrays; deterministic from the seeds); the T6 arrays (≈361 MB) are **not committed** — SHA-256 manifest `docs/audit/raw/t6_MANIFEST_sha256.txt` and `t6_README.md`, regenerate with `t6_alt.py` (all counts/CIs derived from them are in the committed `t6_*.csv`), `raw/t10_D*.csv`, `raw/t1_phi0*.csv`, `raw/t3_S_phi*.csv`, `raw/t3_C_phi0.0.csv`, config JSON beside each run. Analysis outputs: `t6_size.csv, t6_power.csv, t6_lrv.csv, t6_mde80.csv, t7_gaps_size.csv, t8_holm_decomposition.csv, t8_holm_check.json, t9_gates.csv, t10_drift_summary.csv, t3_*`. SHA-256: `docs/audit/SHA256SUMS.txt`. No-touch proof: `docs/audit/NO_TOUCH_LOG.md`, `no_touch.json` (re-generated).
* Known limitations of the tooling: the batched bootstrap is bit-identical to production only for equal trade counts (the unequal-count study T7 uses its own bit-faithful ratio implementation); numba is an optional audit-only dependency; fixed-b reference distributions are regenerated from seed (10⁶ draws per K) and not stored.
* All simulations are synthetic; no confidence is claimed about real-market dependence, edge or calibration.

