# QuantLab — Independent Statistical Audit (synthetic only)

Status: **diagnosis and measurement only. No fix, no protocol change, no production change, no merge, no DEV/VALID/HOLD.**
Code studied: production code at PR #5 head `576fe515fe4b3aa2bf8d14a9cef7ed0d8ad7994a` (branch `hypotheses-dev`).
Production files are byte-identical to that commit (SHA-256 in `docs/audit/NO_TOUCH_LOG.md`; e.g. `events.py` 96e1214b…, `registry.py` e4d3484b…, `experiment.py` d3353b32…, `engine.py` 0711db22…, `stats.py` 5d14932f…).
Protocol v1.2 fingerprint untouched (`08aaa092…26fc`). Registry: 20 events, 0 trials, 0 hold_access.

---

## 0. الخلاصة (Arabic executive summary)

1. **لا أعلن أن المختبر جاهز لـ DEV.** النتائج البرمجية سليمة، لكن الاستدلال الإحصائي لـ Bootstrap الشهري **غير معاير** (تضخم يصل إلى 3× عند 24 شهراً مستقلاً، و8–18× مع ارتباط ذاتي 0.7، و50–100× مع استمرار أنظمة الربح/الخسارة)، وهذا يُنتج FWER فعلياً أعلى من 0.10 على عائلة الـ82 (0.15 في أبسط حالة؛ 0.27 مع استمرار الأنظمة؛ 0.59 مع AR 0.7 وفرضيات مستقلة).
2. **المشكلة في صلاحية الاستدلال نفسه وليس في عدد إعادة السحب:** 100000 إعادة سحب تعطي نفس الانحياز تقريباً (مثلاً 9.2× مقابل 8.7×)؛ ما يتحسن هو الضجيج فقط. السبب: إعادة سحب الأشهر كأنها مستقلة تُهمل الاعتماد بين الأشهر (Design effect حتى 4.1)، مع عدد أشهر صغير (VALID ≈ 24 شهراً) يجعل الذيل غير مستقر. عند الاستقلال يتحسن مع زيادة عدد الأشهر (K=6: 10.9×، K=24: 1.5×، K=60: 1.07×) أما عند وجود اعتماد فلا يتحسن مع K.
3. **Holm منفَّذ بشكل صحيح** (0 اختلاف مع `stats.holm` في 3000 فحص؛ ومع p صالحة تماماً FWER ≤ 0.10 في كل درجات الارتباط). التضخم مصدره قيم p الفردية.
4. **مقارنة الأحداث (event study):** الماكينة نفسها معايَرة (عندما يُولَّد الحدث الملاحَظ بنفس المُولِّد: نسب 0.8–1.06 والفواصل تحتوي 1). التضخم الذي رأيناه في الجولة السابقة **كان جزئياً أثراً لتصميم المحاكاة** (عدم تطابق الدعم بين الأحداث والضوابط) وليس عيباً في الترتيب الجشع. بعد إزالته يبقى أثر صغير لهندسة الوضع العشوائي المتتالي (≈ +0.02 إلى +0.04 في تباين z) لا يُرى بوضوح إلا عند φ=0.95 مع الدعم غير المطابق. لكن **صحة p للأحداث الحقيقية تعتمد على نموذج توقيت الأحداث**: الأحداث المتجمعة (clustered) تعطي تضخماً 1.4× عند 0.10 و4.5× عند 0.001 ضد المرجع الموحد (p_prod وBesag–Clifford كلاهما)، والأحداث المنتظمة تعطي محافظة شديدة؛ المرجع المزاح (circular shift) بقي معايَراً في كل الحالات. لذلك لا يمكن ادعاء معايرة لأحداث حقيقية دون نموذج لتوقيتها.
5. **مقارنة الصفقات بالضوابط:** معايَرة ومحافِظة قليلاً في كل الحالات الصفرية المختبرة (نسب 0.7–1.05 عند 0.10؛ لا تضخم)، والتحجيم العشوائي (subsample) إلى عدد الصفقات الحقيقية ضروري (دونه تضخم 1.2–1.6×). الدقة 1/501 تعني أنه لا يمكن استنتاج شيء أدق من ≈0.002.
6. **توصية:** لا دمج لـ PR #5 ولا بدء DEV إلى أن تقرر أنت (بعد مراجعة ChatGPT) إصلاح/استبدال استدلال الـ Bootstrap على مستوى الاستراتيجية أو التعويض عن ضعفه (أنظر E). لم أنفّذ أي تغيير.

---

## 1. Scope, constraints, and what was NOT done

Constraints honoured (verified by `docs/audit/NO_TOUCH_LOG.md`, `no_touch.json`):

* no DEV/VALID/HOLD, no market data, no experiment registries opened (runtime `sys.addaudithook` guard: 959 opens seen, 0 blocked, forbidden path opened = False; static AST scan: 0 forbidden imports; registry hashed from bytes by a separate process);
* no production file modified; the audit lives in new files only (`src/quantlab/audit/`, `scripts/audit/`, `tests/test_audit_*.py`, `docs/audit/`);
* no protocol/threshold/split/82-family change; no PR created; PR #4 and #5 not merged; `--allow-unverified-specs` unused;
* earlier calibration results (`docs/calibration_raw/*`, `CONTROL_*_CALIBRATION*`) are untouched; unfavourable results were not replaced.

Honest list of what was planned but **not run** (machine restarts killed long jobs; the final queue was reduced and sample sizes are stated in each table):

* T1 ablation at φ=0 and φ=0.5 (run at φ=0.8, φ=0.95 and a stochastic-vol/2-year-strata series);
* S-mode (production-sampler-matched null) only at φ=0.8; not at φ=0, 0.5, 0.95;
* the "extended" G-mode re-runs to reach 30000 studies at φ=0.8/0.95 (G φ=0.8 has 20000, φ=0.95 has 6000, φ=0.5 has 8000, φ=0 has 20000 studies);
* BC reference at C/R mode used 4000 studies and Besag–Clifford at tail levels is only evaluated on studies with k<3000 (`BC_NFULL`);
* trade-control sparse / regular settings: 800 studies each (regular ended at 800; 96 % of its repetitions executed fewer controls than real trades, see C).

Everything is synthetic. Tests: `tests/test_audit_equivalence.py`, `test_audit_bootstrap_equiv.py`, `test_audit_trade_equiv.py` (audit copies of production routines are bit-identical to production), `test_audit_theory.py` (exact enumeration for Lemma 2). All pass.

## 2. A — Event comparison calibration

### 2.1 Mathematical validity and exchangeability (`docs/audit/EXCHANGEABILITY.md`)

The event-study p-value `p = (1 + #{ctrl ≥ obs}) / (1 + M)` is super-uniform (valid) **iff**, under H0, the observed statistic and the M control statistics are exchangeable given the series and the event template (count k, gap rule, eligibility window). Three references were separated:

* **R-S (matched null):** the observed config is drawn by the production sampler itself. Then exchangeability holds by construction; this validates the machinery (rank lemma), not the null model.
* **R-G (unconditional G):** i.i.d. uniform bars → sort → greedy gap-dedupe. Conditional on k, uniform over gap-feasible configurations except a last-shadow boundary truncation (Lemma 2, proven and checked by exact enumeration). Equivalent to a null "event timing carries no information".
* **R-U (conditional-uniform):** Besag–Clifford reversible chain targeting the uniform law on gap-feasible configurations; p_bc is exact for any mixing of the chain.
* **Shift reference:** circular shifts of the event set against the fixed series; exact under "event timing independent of series", resolution 1/(L−1) ≈ 1/1581.

Lemma 3 (production placement): the production sampler (random-order sequential placement in retry/rejection mode) is **not** the uniform law on feasible configurations: it produces ≈7 % fewer close pairs (≤7 bars: 22.1 vs 23.7 at k=98). This is a property of random sequential adsorption, not of the order (time/reverse/per-draw orders are indistinguishable).

**Conclusion on validity:** for *real, rule-based* events no reference can be *proven* exchangeable with the observed events without a model of their timing law. The audit therefore measures sensitivity across timing laws (below) and makes **no calibration claim for real events**.

### 2.2 Why was p_prod optimistic in the round-4 study? (ablation, 1500 studies per config; excess z-variance vs exact G, `docs/audit/t1_table_*.csv`)

| factor | φ=0.8 | φ=0.95 | reading |
|---|---|---|---|
| PROD (production) | +0.039 (SE 0.014) | +0.136 (0.021) | observed excess |
| UNIF_domain / Gk (exact laws on matched support) | +0.003 | +0.005 | exact laws remove it |
| UNIF_window (exact uniform law, **mismatched support**) | +0.038 | +0.132 | ≈ PROD ⇒ support mismatch carries most of it |
| PROD_domain (production sampler, matched support) | +0.020 (0.006) | +0.044 (0.009) | sampler-geometry residual |
| gap rule | needed: no-gap controls over-conservative (sd ratio ≈1.33, ratio@0.05 ≈0.23) | same | the gap is not the problem; removing it is worse |
| order (time / reverse / per-draw / random) | no effect | no effect | **greedy/order is not the cause** |
| retry budget | no effect | no effect | |
| strata (hour / vol / year) | no effect | no effect (SV 2-year series: PROD +0.034, SE 0.015) | |

Candid correction: in round 4 the events were generated over the domain `[60, n−50)` while controls were drawn over the entire eligible window. That design mismatch (not the production logic) produced most of the observed optimism. After support matching, the remaining sampler effect is small (+0.02 / +0.044 in z-variance), consistent with the 7 % close-pair deficit of Lemma 3.

### 2.3 Tail calibration (exceedance rate = P(p ≤ level) under H0; ratio = actual/nominal; exact Clopper–Pearson 95 % CIs; raw per-study CSVs in `docs/audit/raw/t3_*.csv`; full table `docs/audit/TABLES.md`)

Study counts: levels 0.10/0.05 use the first 3000 studies (cheap pre-screen valid for p>0.02), levels ≤0.01 use all studies. A level whose expected exceedances are < ~20 is flagged NOT RESOLVED. **Level 0.001 is not resolvable in any run except as a coarse bound** (≤ 20–30 expected events; MDR80 1.7–2.3).

| model (what generated the observed events) | studies | p_prod ratio @0.10 / 0.05 / 0.01 / 0.005 / 0.0025 / 0.001 | p_bc | p_shift |
|---|---|---|---|---|
| **S** matched null, φ=0.8 | 5000 / 20000 | 1.02 / 1.04 / 0.92 / 1.06 / 0.98 / 0.80 (all CIs contain 1) | n/a | 1.04 / 1.00 / 0.87 / 0.92 / 0.76 / 0.75 |
| **W** support-matched G, φ=0.8 | 3000 / 8000 | 0.92 / 0.97 / 0.88 / 0.88 / 0.80 / 0.75 (CIs contain 1) | n/a | 0.90 / 0.93 / 0.89 / 0.80 / 0.60 / 0.25 |
| **W** support-matched G, φ=0.95 | 3000 / 20000 | 1.00 / 1.05 / 1.04 / 0.86 / 0.84 / 0.95 (CIs contain 1) | 0.97 / 1.01 / 0.92 / 0.80 / 0.96 / 0.80 | 0.97 / 0.97 / 0.92 / 0.78 / 0.86 / 0.60 |
| **G** (support-mismatched) φ=0 | 3000 / 20000 | 1.00 / 0.91 / 0.96 / 1.00 / 1.04 / 1.30 (consistent) | 0.98 / 0.96 / 0.98 / 1.08 / 1.52 / 2.00 (not resolved) | 1.01 / 0.97 / 0.91 / 0.86 / 0.82 / 1.20 |
| G φ=0.5 | 3000 / 8000 | 0.93 / 1.01 / 1.05 / **1.35** / **1.70** / **2.00** (anti-conservative [1.01,1.76],[1.18,2.37],[1.14,3.25]) | 0.94 / 0.97 / 1.02 / 1.28 / 1.84 / 2.00 | 0.95 / 0.97 / 0.96 / 1.18 / 1.25 / 0.88 |
| G φ=0.8 | 3000 / 20000 | **1.04 / 1.08 / 1.16 / 1.25 / 1.40 / 1.50** | 0.97 / 0.96 / 1.06 / 1.22 / 1.34 / 1.35 | 1.00 / 1.01 / 0.99 / 0.96 / 0.82 / 0.80 |
| G φ=0.95 | 3000 / 6000 | **1.11 / 1.18 / 1.37 / 1.60** / 1.20 / 1.67 (last two unresolved) | 0.93 / 0.98 / 1.00 / 1.13 / 0.93 / 0.83 | 0.98 / 0.99 / 0.80 / 0.83 / 0.87 / 0.67 |
| **C** clustered events, φ=0.8 | 2000 / 6000 | **1.39 / 1.60 / 2.32 / 2.60 / 3.13 / 4.50** | **1.34 / 1.60 / 2.23 / 2.70 / 3.20 / 3.25** | **1.04 / 0.99 / 0.90 / 0.80 / 0.67 / 0.83** |
| **R** regular-spaced events, φ=0.8 | 2000 / 6000 | 0.61 / 0.50 / 0.25 / 0.07 / 0.13 / 0.00 (conservative) | 0.54 / 0.48 / 0.17 / 0.10 / 0 / 0 | 1.00 / 1.04 / 1.02 / 1.17 / 1.07 / 0.67 |

Paired comparisons (same studies; McNemar exact + multinomial-bootstrap CI on the count ratio): at G φ=0.95 p_prod exceeds p_bc by 1.19 / 1.27 / 1.37 / 1.41 at 0.10 / 0.05 / 0.01 / 0.005 (McNemar p < 0.03 at each); at G φ=0.8 vs the exact-G reference p_ref by 1.04 / 1.06 / 1.13 at 0.10 / 0.05 / 0.01 (McNemar 0.004 / 0.002 / 0.013). In the support-matched W mode paired ratios are 0.89–1.09 with CIs mostly containing 1 (W φ=0.95 @0.01: 1.094 [1.005, 1.193], McNemar 0.054; @0.10 vs p_bc 1.027 [1.006, 1.052]).

### 2.4 Is the problem confined to one synthetic model?

* **Machinery:** no. With the observed config drawn from the production sampler itself (S) and with the support matched (W), p_prod is calibrated at φ=0.8/0.95 within the resolvable range (levels 0.10 down to ~0.0025). Residual sampler-geometry effect: small (≤ +0.04 in z-variance), detectable only with ≥ several thousand paired studies and large φ.
* **Reference model: yes, it is model-dependent and the dependence is the larger risk.** Against the uniform-timing reference, event sets whose timing is *clustered* (Neyman–Scott) are rejected 1.4× too often at 0.10 and 4.5× too often at 0.001 — for both p_prod and the exact Besag–Clifford reference, so this is not a sampler defect but a null-model mismatch. Regular-spaced event sets are conservative (0.07× at 0.005). The circular-shift reference stayed calibrated in every timing model tested (ratios 0.6–1.2, all CIs consistent with 1 or conservative), because shifting preserves the event template.
* Consequence: **p_prod is valid only to the extent real rule-based events (e.g. D1/H4 pattern triggers) behave, under H0, like a uniform-timing configuration.** Real triggers are plausibly clustered (volatility clustering, trend persistence), i.e. toward the C-mode failure direction.

## 3. B — Monthly cluster bootstrap and strategy p-values

Production: monthly clusters (months with ≥ 1 trade), centred null, `p = (1 + #{null ≥ obs}) / (1 + 5000)` with fixed seed 12345 (common index matrix across hypotheses); minimum p 1/5001 = 0.0002.

### 3.1 Calibration (60000 reps per scenario; K=24 months, 120 trades; `docs/audit/t4_bootstrap_table.csv`)

| scenario | ratio @0.10 | @0.01 | @0.00125 [CI] |
|---|---|---|---|
| A1 iid normal | 1.11 | 1.63 | **2.97** [2.60, 3.39] |
| A2 iid, rr=2 trade outcomes | 0.86 | 1.02 | 1.65 [1.38, 1.97] |
| A4 iid t3 | 1.10 | 1.34 | 1.69 |
| B1 AR(0.3) rr2 | 0.96 | 1.30 | 2.07 [1.75, 2.42] |
| B2 AR(0.7) rr2 | 1.41 | 3.25 | **8.28** [7.64, 8.95] |
| B3 AR(0.7) normal | 1.84 | 5.70 | **17.9** |
| C1 month effect 0.5 | 1.05 | 1.40 | 2.40 |
| C2 month eff. 0.5 + AR 0.5 | 1.72 | 4.68 | 13.4 |
| C3 month eff. 0.5 + AR 0.8 (regime persistence) | 2.58 | 12.0 | **50.8** [49.2, 52.4] |
| C4 month eff. 1.0 + AR 0.8 | 3.16 | 19.4 | **105** |
| D1 / D2 vol heterogeneity (iid) | 1.01 | 0.87 / 0.46 | 0.67 / 0.23 (conservative) |
| D3 vol 1.0, AR 0.7, MA 0.8 | 1.72 | 2.40 | 3.33 |
| E1 / E2 win/loss streaks (0.9 / 0.97) | 1.46 / 2.43 | 3.33 / 11.3 | 8.16 / 48.5 |
| F5 K=12 | 0.86 | 1.42 | 3.41 |
| F6 K=60 | 0.89 | 0.92 | 0.92 [0.72, 1.16] |
| G1–G5 sparse/irregular trades per month | 0.99–1.16 | 1.27–2.61 | 1.84–8.16 |

(Share of p at the floor 1/5001: 0.1 % iid → 3.6–9.3 % in the regime scenarios.)

### 3.2 Mathematical/statistical cause

1. **The resampling treats months as i.i.d.** It preserves within-month structure but not cross-month dependence. Under AR(ρ) or regime persistence the true variance of the mean is larger than the iid-bootstrap variance. Measured design effect = true Var(mean)/bootstrap Var(mean): iid 1.04, AR0.3 1.16, AR0.7 1.7–2.1, regime persistence 2.6 → 4.1, streaks 1.5–1.7, **independent of K** (`docs/audit/t4c_table.csv`). A p-value computed with a variance too small by a factor DE is anti-conservative in proportion (the z-score is inflated by √DE; in a normal-like tail that multiplies exceedance probability by more than DE at p≈10⁻³).
2. **Small-K tail instability under iid.** With K=24 clusters the centred bootstrap uses a plug-in sd from the same sample and the null distribution has heavier-than-normal tails in the studentization effect: inflation at 0.00125 under iid is 10.9× (K=6), 3.3× (12), 2.0× (18), 1.47× (24), 1.23× (36), 1.07× (60), 0.99× (120) for rr2 outcomes (normal outcomes: 23× → 1.15×). It vanishes as K grows **only when months are independent**.
3. **Under dependence, inflation does not shrink with K** (C3 ≈ 45–53× at every K from 6 to 120; AR0.7 5.5× even at K=120; streaks 4.5×): the defect is *invalid inference*, not a Monte-Carlo or finite-resample artefact.
4. **Volatility heterogeneity** (iid but varying variance) makes the bootstrap *conservative* at K=24 (0.2–0.4×) — but an oracle z-test with the true sd is anti-conservative there (5.3×), i.e. the conservatism is accidental.
5. **Number of resamples:** at B2, ratio@0.00125 = 8.0 (1000), 8.72 (5000), 9.12 (20000), 9.16 (100000); C3 52.7× vs 51.2× (100000 vs 5000). More resamples do not fix the bias. They reduce decision noise: P(reject) when the limiting p equals the threshold 0.00125 is 0.41 at 5000, 0.49 at 100000 (0.5 is the ideal); for true p = 0.0015 it is 0.24 (5000) vs 0.016 (100000); disagreement between 5000 and 100000 resamples at 0.00125 ≈ 10 % of rejections (iid) and ≈ 15 % at B2 (11 + 22 of 240).
6. **Precision at 5000:** relative SD of p̂ ≈ 40 % at p*=0.00125; the floor (1/5001) is adequate in principle but the Holm decision at ≈ 0.00125 is noisy.

### 3.3 Alternatives evaluated diagnostically at K=24 (not implemented; `docs/audit/t4c_table.csv`)

| ratio @0.00125 | production boot | t on month totals | Newey–West (lag 3) | circular block bootstrap (b=3) | oracle z (true sd) |
|---|---|---|---|---|---|
| A1 iid normal | 3.31 | **1.17** | 4.77 | 8.11 | 1.20 |
| A2 iid rr2 | 1.47 | 0.53 | 3.57 | 4.69 | 1.23 |
| B2 AR0.7 | 8.27 | 3.81 | 4.37 | 7.79 | 2.11 |
| C3 regime AR0.8 | 50.4 | 32.9 | 29.6 | 46.9 | **1.17** |
| E1 streaks | 7.97 | 3.68 | 6.83 | 11.9 | 0.72 |
| D2 vol 1.0 | 0.40 | 0.27 | 1.17 | 2.16 | 5.28 |

Reading: with only 24 months, Newey–West and block bootstraps are *not* reliable (they need many blocks); the t-test repairs the iid small-K case but not dependence; the oracle shows that a correct *variance* would calibrate everything except mixed volatility — i.e. the missing ingredient is a good estimate of the long-run variance, which 24 months cannot supply for strongly persistent series.

## 4. C — Trade-control comparison

Null: random-timing signals (G gap 1) with random sides, 800 studies per setting; the production `matched_control` (500 reps, two random picks per spec from the same-stratum pool with same side / stop in ATR / RR / max_hold, engine overlap skipping, random subsample to n_real, `p = (1+#{means ≥ obs})/(1+len)`, resolution 1/501). Audit copy verified equal to production.

| setting | mean real trades | mean executed controls (before subsample) | too-few-controls share | p_prod ratio @0.10 [CI] | @0.05 | p_nosub @0.10 |
|---|---|---|---|---|---|---|
| φ=0 mid | 48.6 | 61.4 | 0.0001 | 0.81 [0.63, 1.02] | 0.83 | 1.19 |
| φ=0.8 sparse | 35.8 | 59.1 | 0 | 1.05 [0.85, 1.28] | 1.05 | 1.60 |
| φ=0.8 mid | 56.2 | 81.5 | 0 | 1.05 [0.85, 1.28] | 0.90 | 1.49 |
| φ=0.8 crowded | 97.0 | 116.6 | 0.0002 | 0.78 [0.60, 0.98] | 0.73 | 1.16 |
| φ=0.95 mid | 58.1 | 87.8 | 0 | 0.69 [0.52, 0.89] | 0.80 | 1.19 |
| φ=0.8 regular-stress (fixed 14-bar spacing, controls forced to execute fewer trades than real) | 58.7 | 51.9 | 0.96 | 0.70 [0.53, 0.90] | 0.65 | 0.70 |

Findings:

* **Type-I error:** no anti-conservatism detected at 0.10/0.05 in any tested null (upper CI bounds 0.9–1.4; point ratios 0.65–1.05). Mild conservatism in several settings.
* **Matching and variance:** control/reference sd ratio ≈ 0.985 (0.95–1.05), control hold ratio ≈ 1.0; var_z 0.92–1.05 except regular-stress 0.78.
* **Non-overlap + redraw:** executed controls are 1.2–1.5× the real trades in normal settings, so the subsample is always available; in the stress case (regular signals) 96 % of repetitions have fewer controls than real trades and p becomes conservative, not liberal.
* **Subsample selection matters:** without the random subsample to n_real (`p_nosub`) the test tends to be anti-conservative (point ratios 1.16–1.60× at 0.10, CI lower bounds ≈0.97–1.2, i.e. clear only in the sparse/mid settings; up to 2.1× at 0.05 in sparse), because the control mean then has a smaller variance than the real mean. The production subsample is therefore a required part of validity.
* **Resolution:** p takes values in multiples of 1/501 ≈ 0.002; one cannot conclude anything below ≈ 0.002 and the Holm threshold of 0.00125 is below the grid (a p of 1/501 = 0.002 can never be rejected at 0.00125). Tail levels ≤ 0.01 were not resolvable with 800 studies (≤ 8 expected exceedances; reported but not conclusive).
* Limit of the evidence: only random-timing / random-side nulls were tested; no timing-dependent or trend-dependent nulls and no strategy-specific stop/RR laws. Calibration for real signals is **not** claimed.

## 5. D — Holm and the 82-family

* **Holm implementation:** independent re-implementation vs `stats.holm`: 0 mismatches in 3000 random cases (including ties, padding to m = 82 with p = 1 for missing). `registry.family_table` follows the production rule (missing p → 1).
* **Holm with exactly valid p** (uniform p-values; 82 hypotheses; α = 0.10): FWER 0.096 (ρ=0), 0.048 (ρ=0.5), 0.010 (ρ=0.9), 0.003 (ρ=0.99) — never above 0.10; dependence between hypotheses only makes Holm more conservative. Holm is *not* at fault.
* **Production bootstrap p-values (2500 simulated families per row; shared month effects / volatility / streaks across strategies; ρ = between-strategy latent correlation):**

| scenario | ρ | selection | FWER (Holm, 0.10) [CI] | mean false rejections (Holm) | per-test false rate at raw p ≤ 0.10/82 vs nominal | power (true δ=0.5) |
|---|---|---|---|---|---|---|
| iid rr2, full null (82 null) | 0 (5 true effects) | all 82 | **0.151** [0.137, 0.166] | 0.164 | 1.75× | 0.77 |
| iid rr2 | 0.5 | all 82 | 0.095 [0.084, 0.107] | 0.140 | 1.40× | — |
| iid rr2 | 0.9 | all 82 | 0.042 | 0.126 | 1.18× | 0.77 |
| iid rr2, mixed (20 true) | 0.5 | all 82 | 0.091 | 0.144 | 1.68× | 0.79 |
| AR(0.3) rr2, full null | 0.5 | all 82 | **0.100** [0.089, 0.112] | 0.182 | 1.82× | — |
| AR(0.3) rr2, 5 true | 0.5 | all 82 | 0.108 | 0.217 | 2.27× | 0.56 |
| AR(0.3) rr2, 20 true | 0.5 | all 82 | 0.110 | 0.178 | 2.03× | 0.57 |
| AR(0.7) rr2 (independent strategies, common idx) | 0 | all 82 | **0.589** [0.569, 0.608] | — | — | — |
| AR(0.7) rr2 | 0.5 | all 82 | 0.240 | — | — | — |
| regime persistence C3 (month eff. 0.5, AR 0.8), full null | 0.5 | all 82 | **0.274** [0.257, 0.292] | 5.84 | 48× | — |
| C3, 5 true effects | 0.5 | all 82 | 0.269 | 6.18 | 54× | 0.56 |
| staged DEV-screen (raw p ≤ 0.10) → VALID (fresh data) iid | 0.5 | staged | 0.058 [0.050, 0.068] | 0.078 | 1.68× | 0.77 |
| staged, AR(0.3) | 0.5 | staged | 0.057–0.061 | 0.088 | 1.9–2.1× | 0.57 |
| staged, C3 | 0.5 | staged | **0.185** | 2.91 | 51× | 0.53 |

* Effect of dependence **between hypotheses**: reduces the FWER of Holm when p-values are valid (0.096 → 0.003) and reduces it for the production p-values too (0.151 → 0.042 for iid), but it also concentrates false rejections (all-or-nothing within a family), so a single event can invalidate many findings together. It does not repair the per-test inflation; with persistent regimes (C3) the FWER stays 0.27 even with dependence.
* Staged selection (DEV screen then VALID on fresh data) roughly halves the FWER relative to testing all 82 on VALID alone for iid / AR(0.3) cases, but the regime-persistence case still gives 0.18. VALID data are used once; this does not give a second look.
* Power under tested scenarios: 0.77–0.79 (iid) and 0.53–0.57 (AR 0.3 / regime), at an effect δ = 0.5 per-trade sd units, K = 24 months, 5 or 20 true hypotheses. The inflated size is bought without power gain, because the Holm cut-off ≈ 0.00125 relies on the tail precisely where the bootstrap is least accurate.

## 6. E — Assessment of readiness for DEV (no decision taken)

**The laboratory is not shown to be ready for DEV.** Software tests passing does not establish inferential safety. Findings per problem, with alternatives and trade-offs (nothing implemented):

### E1. Monthly bootstrap / strategy p (axis B) — **defect (size: large)**
* Size: 1.5–3× at K=24 under independence, 2–18× under AR 0.3–0.7, 8–100× under persistence/streaks at the Holm threshold; family FWER 0.15–0.59 against a nominal 0.10.
* Impact: false positive findings in VALID at the Holm cut-off.
* Alternatives (statistical, with pros/cons):
  1. *Studentized/t month-total test with Student df = K−1* — fixes iid small-K tail (ratio 1.17 at 0.00125); cheap and transparent; does **not** fix persistence (33–38× in C3).
  2. *Effective-sample-size / design-effect-corrected variance (AR or batch-means)* — addresses variance inflation; requires an estimate of ρ from K = 24 points (noisy); risk of under-correction; evaluate by simulation.
  3. *Block / stationary bootstrap* — no gain at K=24 in the experiments (4–47× at 0.00125); would need K ≥ 60.
  4. *Randomization / permutation against matched controls with time-block (regime-preserving) permutation* — exact under exchangeability of blocks; needs a defensible exchange scheme; resolution limited by permutations.
  5. *Raise the evidence bar instead of the test:* require both a corrected test and out-of-time confirmation; Pros: no distributional assumptions; cons: needs more data / months.
  6. *More months (K ≥ 60) or pooling VALID with a longer window* — shrinks the iid inflation (≈1.07×) but **not** the dependence-driven inflation (C3 ≈ 51× at K=120).
  * More resamples (100000) reduces decision noise only; it cannot fix the bias.

### E2. Event comparison (axis A) — **machinery OK; reference-model risk (size: model-dependent)**
* Size: negligible-to-small for a matched null; up to 1.4× at 0.10 and 4.5× at 0.001 for clustered events against any uniform-timing reference (p_prod and p_bc alike); conservative for regular events. Round-4 tail optimism was largely a support-mismatch artefact of the simulation design.
* Alternatives: (a) keep p_prod but restrict its use to screening (the DEV screen uses raw p ≤ 0.10 where excess is ≤ +4–8 %), never as a final significance statement; (b) circular-shift reference (exact for "timing independent of series", calibrated in every model tested; cons: resolution 1/1581, destroys relation to calendar/session features unless the shift is block-aware); (c) Besag–Clifford conditional-uniform reference (exact for any mixing; cons: still a uniform-timing null, fails for clustered events); (d) sampler with the exact uniform law (removes the small geometry effect; changes production sampler).

### E3. Trade-control (axis C) — **no defect found in tested nulls**
* Size: none detected; conservative by 0–30 %. Subsample to n_real is essential. Precision 1/501 limits conclusions to p ≳ 0.002.
* Alternatives: if tail inference is ever needed, increase the number of control repetitions (≥ 5000 for 1/5001) or use an analytic/permutation reference; cost: runtime. Evidence is limited to random-timing nulls.

### E4. Holm / 82-family (axis D) — **Holm correct; FWER bound fails because individual p are inflated**
* Size: FWER 0.15 (iid), 0.27 (persistent regimes), 0.59 (AR 0.7, independent strategies) vs 0.10.
* Alternatives: fix individual p first (E1); until then do not interpret Holm output as a controlled FWER; if a conservative guard is desired, an e.g. effective-test count, or a stricter threshold calibrated by simulation (pros: simple; cons: costs power, which is already 0.53–0.79).

### E5. Merge readiness of PR #5 and DEV readiness
* **PR #5 (hypotheses-dev):** no defect in event/trade machinery was found; the main inferential defect (E1) lives in `stats.cluster_bootstrap`, which is shared production code. I do not recommend merging or starting DEV until you decide how to address E1; I have changed nothing.
* **DEV:** DEV screen uses the event p ≤ 0.10 where the measured excess is ≤ ~+10 % in support-matched nulls but up to +40 % for clustered events. The more serious exposure is at the VALID/final stage (Holm over bootstrap p).
* Decisions on protocol, mechanism change, merge, DEV start are reserved to you and the independent reviewer.

## 7. Reproducibility

* Environment: Python 3.13, numpy/pandas/scipy, numba (audit-only, for `bc.py`), editable install `pip install -e .`; run from the project root with `PYTHONPATH=src`.
* All runners are resumable and deterministic; seeds are in `src/quantlab/audit/tail.py` (`DEFAULT_SEEDS = {"G": 100000, "S": 400000, "C": 500000, "R": 600000, "W": 900000}`, series seed 200000 for G φ=0.95 to match the old CSV), in each run's `*.config.json` (`docs/audit/raw/`) and in `t4_bootstrap.py` / `t4c_extended.py` (`SEED0`, per-scenario `default_rng([SEED0, scenario_index, chunk])`; bootstrap n=5000, seed 12345).
* Commands (see `scripts/audit/run_queue*.sh`):
  ```
  PYTHONPATH=src python3 scripts/audit/t1_ablation.py --setting phi0.8 --n 1500
  PYTHONPATH=src python3 scripts/audit/t3_tail.py --mode {G,S,C,R,W} --phi 0.8 --n 20000 --nfull 3000
  PYTHONPATH=src python3 scripts/audit/t2_bc.py --mode G --phi 0.95 --n 20000
  PYTHONPATH=src python3 scripts/audit/t3_shiftfill.py --phi 0.95
  PYTHONPATH=src python3 scripts/audit/t4_bootstrap.py --reps 60000
  PYTHONPATH=src python3 scripts/audit/t4b_extra.py --part a ; ... --part b --fams 2500
  PYTHONPATH=src python3 scripts/audit/t4c_extended.py ; t4d_family.py ; t5_trade.py --setting phi0.8_mid --n 800
  PYTHONPATH=src python3 scripts/audit/{t1,t3,t4,t4c,t4d,t5}_analyze.py ; build_tables.py ; no_touch_proof.py
  PYTHONPATH=src python3 -m pytest tests/test_audit_*.py
  ```
* Raw outputs: `docs/audit/raw/**` (per-study CSV; bootstrap rejection counts as NPZ). Analysis tables: `docs/audit/*.csv`, `*.json`, `TABLES.md`. Theory: `docs/audit/EXCHANGEABILITY.md`. File hashes: `docs/audit/SHA256SUMS.txt`. No-touch proof: `docs/audit/NO_TOUCH_LOG.md`, `no_touch.json`.
* Interpretation caveats: all results are synthetic; ratios near 1 at levels with < 20 expected events are not proof of calibration; confidence intervals are exact (Clopper–Pearson) per cell and not adjusted for the number of cells; no claim of edge or of calibration on real data is made.
