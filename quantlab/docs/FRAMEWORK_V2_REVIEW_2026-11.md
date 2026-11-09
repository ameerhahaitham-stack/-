# QuantLab Statistical Framework v2 — Independent Review

Nov 9, 2026 · Author: Claude (independent design review for Ameer) · Review only: no code, no project change, no market data, no simulation run for this document

## الخلاصة بالعربية

**الحكم:** الفكرة العلمية سليمة ويجب الاحتفاظ بها (فصل الحافة الاقتصادية عن المهارة التنبؤية عن الحافة الشرطية، ومنع تجميع الضوابط في p واحد، ومعايرة الإطار اصطناعياً قبل أي تطبيق). لكن المقترح كما هو يخفي مشكلة أكبر من كل ما فيه: **كمية المعلومات المستقلة المتاحة لا تكفي** لتأكيد حافة واقعية، والتقسيم حسب الأنظمة يضاعف هذا النقص.

1. **القوة قبل التقسيم:** نتائج التدقيق السابق (اصطناعية) تعطي حداً أدنى للكشف بقوة 80% ≈ 0.5R للصفقة عند 24 شهراً. حسابياً (نظري)، تأكيد حافة 0.10R عند عتبة Holm يحتاج نحو 3,000+ صفقة *مستقلة فعلياً*، وحتى عند مستوى أعلى من ذلك نحو 1,400–2,300. وهذا خارج ما تستطيع نافذة VALID أو HOLD إنتاجه على D1/H4.
2. **الحافة الشرطية أصعب لا أسهل:** تقليل العينة إلى جزء من الوقت (نظام صاعد مثلاً) يرفع الحد الأدنى للكشف بالنسبة نفسها، وعدد حلقات النظام المستقلة في سنتين قد يكون 3–6 فقط. واختيار النظام الذي أعطى أفضل نتيجة هو نفسه التعددية التي تخشاها.
3. **لا يوجد اختبار نعرف أنه مضبوط:** اختبرنا (اصطناعياً) أن الـ Block Bootstrap أسوأ من Bootstrap الإنتاج عند الذيل (4.7–52× عند K=24)، فلا تفترض أن أي طريقة المتعلقة بالاعتماد الزمني صالحة من اسمها.
4. **التصنيف الخماسي ناقص:** الفئة «غير مؤكد» تخلط بين «الأدلة ضدها» و«العينة لا تكفي أصلاً»، وهذا فرق جوهري. أقترح فئة «غير حاسم — قوة غير كافية» منفصلة.
5. **أصغر نظام مدافع عنه:** ادعاء أساسي واحد معلن مسبقاً لكل استراتيجية، نظام واحد مجمّد، المرشح المفلتر يُعامَل كاستراتيجية جديدة داخل عائلة التعددية، بوابات متتالية (اقتصادية ← مهارة ← شرطية) بكل منها null خاص، وتقرير القوة/MDE مع كل نتيجة.
6. **القرار المطلوب منك قبل أي تطبيق:** ما هي مصادر الأدلة المستقلة المسموح بها؟ نافذة VALID الحالية وحدها لا تكفي؛ الخيارات: أدلة مستقبلية (forward) بعد التجميد، أو نوافذ أطول في بروتوكول لاحق، أو قبول أن النتيجة المعتادة هي «غير حاسم».

لم أعدّل أي ملف في المشروع، ولم أكتب كوداً، ولم أشغّل أي محاكاة جديدة لهذه المراجعة (الأرقام المذكورة إما من تدقيقي السابقين أو حساب نظري موضح بالوسم \[T\]).

## Epistemic status — what is verified, theoretical, proposed

Every claim below carries one tag. **\[V\]** = measured in my two synthetic audits (`statistical-audit-2026-11`, commit 3109813; synthetic only, no market data). **\[T\]** = theoretical or arithmetic argument, not simulated for this review. **\[P\]** = proposed design or future experiment, nothing run. No implementation, no market test, no file in the project was changed for this review.

| Fact used in this review | Tag | Source / basis |
| --- | --- | --- |
| Production monthly bootstrap, tail level 0.00125, K=24 months: 1.4–3× nominal with independent months, 7.9–56× with month-level persistence; K=60 fixes only the independent part (0.8–1.6×), persistence stays 5–53× | V | supplement §2 |
| Circular block bootstrap (block 3) is *worse* than the iid-month bootstrap in the tail: 4.3–7.2× under independence, up to 52× at K=24; 1.5–2.6× and up to 35× at K=60 | V | supplement T6 (`cbb3`) |
| Newey–West (lag 1 / 3) at K=24: 0.4–4× under independence, 6–33× under persistence | V | T6 |
| Group test over 4 contiguous blocks (Ibragimov–Müller): worst case 2.5× (K=24), 1.6× (K=60), but power ≤ 9% at 0.5R/trade at the 0.00125 level | V | T6 |
| Oracle z-test (true variance known): MDE at 80% power, level 0.00125 ≈ 0.50R/trade at K=24, ≈ 0.35R at K=60 | V | T6 |
| Variance estimators from 24 months are biased low by 15–75% under persistence and stay biased at K=60 | V | T6 LRV |
| Holm is arithmetically correct; FWER of 82 null strategies with production p-values is 0.146 (no dependence) to 0.998 (persistent) | V | supplement §4 |
| Dropping empty months makes the effective K = number of active months; unequal trade counts add 4–5× inflation | V | supplement §3 |
| Matched-control p is calibrated at the 0.10 gate under random-timing and drift nulls, but correlated with the bootstrap p (rank corr. 0.53–0.83) | V | T10, with the caveat that an always-long strategy has positive baseline R in the synthetic engine |
| Sample-size arithmetic for MDE and number of effective trades (Section D) | T | standard normal-approximation, trade sd ≈ 1.5R as in the audit generator |
| Every regime-related claim (power per regime, interaction tests, misclassification, selection after search) | P/T | **not measured by anyone yet** — it is the content of the proposed calibration plan |

Rule used throughout: where the audit measured something under a dependence structure *I* chose, it says how the real market may differ — the real dependence of strategy returns is unknown and cannot be learned from VALID or HOLD without destroying them.

## A. Scientific critique

**What is right and should be kept.** Separating economic edge from predictive skill; requiring causal regime labels; refusing a single combined p-value; making synthetic calibration a precondition; stating a preference for no discovery over a false one. These are sound.

**Weaknesses, in order of consequence.**

1. **Information budget is never stated, and it decides everything.** \[T\] With trade sd σ ≈ 1.5R and independent trades, detecting a mean μ at one-sided level α with 80% power needs N ≈ ((zα + 0.84)·σ/μ)² trades. For μ = 0.10R: ≈ 1,400 trades at α = 0.05, ≈ 2,300 at 0.01, ≈ 3,400 at 0.00125 (the Holm-equivalent level of the 82-family). Dependence multiplies N by the design effect DE. A conditional claim divides the usable trades by the regime's share of time. D1/H4 gold and EURUSD over a 24-month VALID window cannot supply this. The proposal says "prefer no confirmed strategy" — with this budget the framework will return "unconfirmed" for essentially every realistic edge, *whatever the truth*. A test that almost cannot say yes is safe but nearly uninformative; the proposal must say so and decide what evidence source fills the gap (Section C, tier 4).
2. **Regime conditioning multiplies hypotheses and removes information at the same time.** \[T\] The family is strategy × parameters × instrument × timeframe × regime definition × regime state × entry/exit variant. "Bullish +0.25R, bearish −0.05R, sideways +0.01R" is the best of three (or more) look-alike subsets: its expected maximum is positive under the null (winner's curse). Cutting a series into 3 regimes also cuts effective information roughly by 3, and with regime persistence what remains is *episodes*, not trades: two calendar years may hold only 3–6 bullish/bearish episodes. The proposal acknowledges multiplicity but does not give the conditional claim a *higher* evidence bar than the general claim; "without weaker evidence requirements" must be operationalised as: the regime filter is part of the strategy definition and is priced into the family.
3. **A regime-conditioned edge is not exogenous to the benchmark.** \[T\] Gold has had long drifts; momentum/persistence means a long-only strategy in a trailing-return "bullish" regime inherits positive expected return from the label alone. The economic-edge claim may be fine (the proposal says so), but the *predictive-skill* control must be regime-matched passive exposure, not a market-wide random control, or the framework will certify beta-in-a-filter as skill. The earlier audit already showed a bootstrap gate passed by always-long, no-timing strategies 3–6% of the time at the 0.00125 level \[V\].
4. **"Predictive skill" is three different nulls.** \[T\] (a) direction skill (long vs short given a signal), (b) timing skill (when, given direction), (c) regime-selection skill (whether to trade in this state). Randomising directions tests (a) and destroys drift structure; random timing with the side kept tests (b); the filtered-versus-unfiltered contrast tests (c). One "matched control" answers none of them cleanly. Each needs its own estimand, null and calibration; none should be combined, as the proposal itself says.
5. **The unit of inference is undefined.** \[V\] The audit showed the target quantity changes with the estimator: the production ratio estimator on active months has an effective K equal to the number of active months (8.9× inflation with \~10 active months and no dependence at all). The proposal must fix the estimand — e.g. expected net R per calendar month with zeros included, or per trade — *before* choosing a test, because empty months, unequal counts and the regime filter all change what is being averaged.
6. **Regime-classifier degrees of freedom.** \[T\] Comparing a "simple predeclared" classifier, an "independent-information" classifier and "alternative reasonable definitions" is itself a multi-way comparison. If all three may produce pass/fail, it is a hidden garden of forking paths. One classifier is primary and frozen; the others are sensitivity reports with no pass/fail role. Also, quantile thresholds computed on the whole sample (volatility terciles) are look-ahead even if every individual label uses only past bars; thresholds must be absolute or expanding-window.
7. **The five-class model gives every strategy several chances to earn a label.** \[T\] If Class 1, 2, 3, 4 are evaluated post hoc, the probability that *some* positive label is awarded is higher than each class's error rate. Fix: each strategy declares one primary claim (general or conditional, economic or skill) before the freeze; secondary labels are descriptive. And "Unconfirmed" merges two different states — *evidence against* (the interval excludes economically relevant effects) and *inconclusive/underpowered* (the interval is too wide to say anything). A framework that cannot tell them apart will discard strategies it never had the power to evaluate.
8. **Component A is a menu without a selection rule, and the menu has already been partly tested.** \[V\] Block bootstraps are not a safe default: circular block bootstrap (block 3) was worse than the production iid-month bootstrap at the 0.00125 tail, in every scenario we ran. HAC and fixed-b are near nominal for independent months but stay inflated under persistent regimes at K=24 (HAC 6–33×, fixed-b 2–9.5×); only a group test (4 blocks) had a size bound, at almost no power. No method here is "adopt-able" on assumptions plus calibration at 24 months.
9. **Instruments and timeframes are not independent.** \[T\] XAUUSD and EURUSD share the USD factor; D1 and H4 versions of one rule share most of their information. Counting them as separate confirmations inflates apparent evidence; counting them as separate hypotheses is correct for multiplicity but they add little independent information for pooling.
10. **Missing scenarios** (additions to the ten): edge decay/non-stationarity (a real edge that disappears), cost-model misspecification, overlapping or position-dependent trades, correlated search (neighbouring parameters), repeated research cycles reusing VALID, and *calendar* effects (month-end, session) in the noise. Scenario 10 (selection) is a special case of 8 and should be run through the same pipeline, with the selection rule written down.
11. **Thresholds are not stated.** The proposal gives no target error rates, no power target, no minimum effect that matters economically. Without them "calibrated" has no pass criterion; Section D supplies proposals, to be decided by you and the reviewer, not tuned afterwards.
12. **Controls are not a substitute for inference on the main effect.** \[V\] In the drift-regime study the control p was well calibrated yet strongly correlated with the bootstrap p, so requiring both gates removes only part of the false passes. Two partly redundant gates are not two independent chances to reject.

## B. Statistical method comparison

Tags: \[V\] measured by me on synthetic data (numbers are ratios of actual to nominal rejection rate at level 0.00125, K=24 months → 60); \[T\] theory; "not tested" = I have no measurement. None is recommended as a stand-alone solution.

### B1. Inference on economic performance (estimand: mean net R)

| Method | Tests | Key assumptions | Strengths | Weaknesses | Suitable when | Fails when |
| --- | --- | --- | --- | --- | --- | --- |
| iid-month cluster bootstrap (production) | mean R ≤ 0 | months exchangeable; variance of month totals stable | simple, handles skew | wrong variance under any cross-month dependence; K−1/K factor | descriptive ranking of strategies | persistence: 7.9–56×, no gain with K \[V\]; sparse months: effective K = active months \[V\] |
| Month-total t-test (K−1 df) | mean of month totals ≤ 0 | independent months, near-normal totals | exact under its assumptions; ≈ nominal for independent months \[V: 0.6–1.0×\] | no dependence correction | independent months, K ≥ \~30 | persistence: 6–47× \[V\] |
| HAC / Newey–West (lag 1, 3) | same, robust to serial correlation | weak stationarity, lag ≪ K, consistent LRV | standard, easy | needs consistent LRV; unreliable at K=24; biased low \[V\] | long samples (K ≥ 100) | K=24: 6–33× under persistence \[V\] |
| Fixed-b (Kiefer–Vogelsang, Bartlett b=1) | same, reference distribution accounts for bandwidth | weak stationarity; reference simulated | best of standard tests in my panel: ≤ 3.1× moderate, 9.5× severe (K=24); 5× (K=60) \[V\] | still anti-conservative, needs simulated reference | moderate dependence | strong regime persistence \[V\] |
| Ibragimov–Müller group test (q contiguous blocks) | block means have mean 0 (t with q−1 df) | blocks approx. independent normal, α ≲ 0.08 | has a size theorem; worst case 2.5× (K=24), 1.6× (K=60) \[V\] | power ≤ 9% at 0.5R, q≈1–4 blocks only; premise unverifiable \[V\] | worst-case size control matters more than power | when power is needed at small α (it has almost none) |
| Moving / circular block bootstrap | same, via resampled blocks | stationarity, block length ≫ dependence range | in principle handles weak dependence | block length is a tuning parameter; with K=24 blocks are 8 draws; *worse than iid bootstrap in the tail*: 4.3–52× (K=24) \[V\] | long series, short memory | short series, persistence, small tails \[V\] |
| Stationary bootstrap (random block length) | same | stationarity, geometric block lengths | less sensitive to the block-length choice than CBB | same limitation; tail behaviour at K=24 expected like CBB | as CBB | not tested; expect the same failure \[T\] |
| Weighted/AR-ESS variance inflation | mean with effective sample size | AR(1) month dependence | simple | lag-1 estimate from 24 points is noisy; persistence 3.8–24× \[V\] | exploratory sizing | non-AR structure, regimes |

### B2. Controls (predictive-skill questions)

| Control | Question it answers | Preserves | Destroys / leaves open | Fails when |
| --- | --- | --- | --- | --- |
| Matched random entry (same side, stop, RR, hold, strata) | timing skill given direction and geometry | drift, volatility, geometry | does not test direction or regime choice | controls matched on an outcome-correlated stratum; correlated with the bootstrap gate \[V\] |
| Randomised direction | direction skill | timing/exposure | destroys drift: a long-only strategy beats a mixed-direction control in any uptrend | any drifting market \[T\] |
| Holding-period-preserving | timing skill without exposing to hold-length effects | exposure time | does not control direction | heavy-tailed trends |
| Exposure-matched (time in market, side) | skill beyond passive exposure | beta | requires a benchmark return series | benchmark itself mis-specified |
| Regime-matched passive benchmark | skill beyond "always long in this regime" | beta *inside the regime* | regime-selection skill assigned to the label, not the signal | label error, label persistence |
| Circular time-shift of signals (calendar axis) | timing independent of the series | the series' full dependence; exact if timing is independent of it \[V in the event study: calibrated in every timing model tried\] | requires signal timing to be *exchangeable under the null* | signals that are functions of the series in a way shifts break (e.g., breakouts) |
| Filtered vs unfiltered paired difference | value of the regime filter | identical signals and costs | not a test of the base edge | filter touches few trades |

### B3. Multiple testing

| Method | Controls | Assumptions | Strengths | Weaknesses | Fails when |
| --- | --- | --- | --- | --- | --- |
| Holm | FWER (any dependence) | valid marginal p-values | uniformly better than Bonferroni; arithmetic verified \[V\] | no more than Bonferroni in power; no use of dependence | marginals invalid: FWER 0.146 → 0.998 with production p \[V\] |
| Max-T / Westfall–Young stepdown | FWER (strong, under subset pivotality) | joint resampling preserves the dependence of the *null*; valid marginals after resampling | uses cross-strategy dependence; power gain over Holm when hypotheses correlate | the resampling must be calibrated across *time* dependence too; heavy computation; not tested here | persistence not preserved by the resample \[T\] |
| Benjamini–Hochberg | FDR (independence / PRDS) | positive dependence | far more power; right for triage | not a family-wise guarantee; a few false positives are expected by design | confirmatory "no false positive" aim \[T\] |
| Benjamini–Yekutieli | FDR (any dependence) | none | valid under arbitrary dependence | costs a log m factor; still not FWER | as above |
| Hierarchical / gatekeeping | FWER along a declared order | order fixed *before* data | spends error only where claims are made; naturally fits Q1→Q2→Q3 | needs declared order and primary hypotheses | order chosen after seeing results |
| Predeclared primary / secondary | by design | discipline | smallest family, largest power | restricts what may be claimed | researcher adds primaries after the fact |
| Alpha-spending ledger across research cycles | cumulative error across reuse of one validation set | records of each exposure | prevents silent reuse | reduces later power | undisclosed reuse |

### B4. Interaction (conditional-edge) tests

| Method | Tests | Assumptions | Weakness | Fails when |
| --- | --- | --- | --- | --- |
| Within-regime mean (Q1 on regime subset) | positive expectancy in the regime | regime exogenous to the noise | selection of the regime after search; low information | regime chosen post hoc \[T\] |
| Regression of trade R on regime dummies with HAC/fixed-b errors | regime differences | as HAC | few independent episodes; dummies are persistent | episodes < \~10 \[T\] |
| Paired filtered-minus-unfiltered monthly difference | value added by the filter | paired design cancels common noise | filter removes most trades → noisy | thin filtered sample |
| Regime-label permutation (permute episodes, not bars) | difference between regimes under exchangeable episodes | exchangeable episodes | a handful of episodes → exact permutation test has coarse p (e.g. 6 episodes → minimum p = 1/20) \[T\] | very few episodes |
| Out-of-sample regime replication | replication of the sign and size | frozen definition | needs new regime episodes in new data | no new episodes arrive |

## C. Recommended architecture — the smallest defensible system \[P\]

Principle: **one declared claim per strategy, one primary test per question, errors spent only along a declared order, and every verdict reports what the sample could have detected.** Nothing here is adopted until Section D shows it holds on synthetic data.

### C1. Four questions, four estimands, four nulls

| Question | Estimand | Null | Primary evidence | Role in classification |
| --- | --- | --- | --- | --- |
| Q1 Economic edge | expected net R per calendar month (zeros included) or per trade — **choose one, once**; stressed-cost scenario reported | μ ≤ 0 | an *interval* for μ from a method that passed calibration across the dependence envelope; economic gate = lower bound ≥ a declared minimum (not just p < α) | Class 1 / Class 2 |
| Q2 Predictive skill | excess net R over the matched benchmark (side, geometry, regime-matched passive exposure) | no timing information beyond the matched benchmark | conditional randomisation (matched entries and calendar-axis circular shifts), reported **separately** for direction, timing, regime selection | Class 3 / Class 4 |
| Q3 Conditional edge (the filter) | paired monthly difference, filtered minus unfiltered, on the same signals and costs | filter adds nothing | paired interval; the regime filter is part of the strategy definition and counts in the family | Class 2 / Class 4 |
| Q4 Feasibility (before testing) | minimum detectable effect and number of independent episodes of the design | — | computed from the frozen design and the dependence envelope, *without looking at strategy returns* | decides "testable" vs "inconclusive" |

### C2. Evidence tiers (existing DEV / VALID / HOLD unchanged; one tier added as a proposal)

1. **DEV — discovery and triage.** Exploratory; every variant tried is counted; FDR-type triage allowed (BH/BY) because nothing is claimed. No confirmatory label can come from DEV.
2. **VALID — confirmation, once per frozen strategy.** Gatekeeping Q4 → Q1 → Q3 → Q2; family-wise error (Holm over a family counted *including regime variants*) because a confirmatory claim must control false positives, not just their rate.
3. **HOLD — final, once.**
4. **Prospective tier (new, needs your decision).** Out-of-sample data that arrive *after* the freeze (paper/live-like trading under the frozen rules). Reason: \[T\] D1/H4 on two instruments cannot generate the 1,400–3,400 effective trades that a 0.10R claim needs inside the VALID+HOLD windows; the only source of fresh independent information is time. This tier accumulates evidence under a pre-registered stopping/spending rule instead of one look.

### C3. Verdicts must be power-aware

Every strategy ends in one of: **Confirmed** (the interval excludes zero and meets the declared economic minimum), **Rejected** (the interval excludes the declared minimum edge), **Inconclusive — insufficient power** (the interval contains both zero and the minimum, and the design's MDE exceeds the claimed effect). The current "Unconfirmed" class is split into these last two.

### C4. Method choices, stated with their assumptions

- **Inference for Q1.** No method has yet been shown to be both calibrated and powered at 24 months \[V\]. Proposed: report two intervals — a *conservative* one from a group/block-mean test whose size bound is a theorem (its price: wide intervals), and a *sensitivity* one from fixed-b — and pre-register that confirmation requires the conservative one. Rationale: false-positive control is the stated priority. If the conservative interval is too wide to ever confirm the claimed effect, Q4 says so in advance and the verdict is "Inconclusive", not a quiet pass.
- **Q2.** Conditional randomisation with the calendar-axis time-shift as the *reference* null (exact when timing is independent of the series \[V in events\]); matched entries as a second, separate report; never merged into one p. Calibrated on Scenario 2 (drift without skill) *before* use \[P\].
- **Multiplicity.** FWER (Holm, or max-T only if its joint resampling is itself calibrated under persistence) for confirmatory tiers; FDR only for DEV triage. The family counts strategy × config × instrument × timeframe × regime variant actually explored. Holm is used because it needs only valid marginals — the marginals are what Section D calibrates.
- **Regimes.** At most two dimensions (direction; volatility), three states each, one primary classifier frozen with causal inputs and absolute (or expanding-window) thresholds; structure (trend/range/breakout) is deferred — it has the most label ambiguity and the fewest independent episodes.

### C5. What is deliberately left out

No combined p-value across controls; no per-regime optimisation of parameters; no regime × regime cross-products; no re-testing of a modified strategy on an exposed validation set; no automatic promotion between classes.

## D. Calibration plan \[P — nothing below has been run\]

### D1. Rules of the program

- Synthetic only; generators written and **frozen with seeds before** any candidate method is evaluated; methods are scored on the whole *dependence envelope*, never on the average of scenarios. A method that fails any envelope cell is reported as failing there.
- Error-rate targets are decided by you and the reviewer **before** the run (proposals below), then not tuned.
- Every rate is reported with exact (Clopper–Pearson) 95% intervals and its simulation count; failed or unfavourable cells are in the main table, not an appendix.
- Fixed-b and other reference distributions are simulated per K; the cost of each method (CPU seconds per 1,000 datasets) is reported.

### D2. Proposed targets (to be approved, not tuned afterwards)

| Quantity | Target | How it is read |
| --- | --- | --- |
| Per-test Type-I error, levels 0.05, 0.01, 0.00125 | upper 95% bound ≤ 1.5× nominal in **every** envelope cell | a cell above 1.5× = the method is not usable there |
| Pipeline FWER (all hypotheses null, confirmatory family) | point ≤ 0.10 and upper bound ≤ 0.12 | measured on the full pipeline (selection + test + multiplicity) |
| FDR in DEV triage | ≤ 0.10 with m null-heavy (≥ 90% null) | triage only |
| 95% interval coverage | lower bound ≥ 0.93 | for μ and for regime contrasts |
| Power | ≥ 80% for the **declared minimum economic effect**; report the full power curve and MDE | if no method reaches it, the declared effect is "not testable at this sample" |
| Misclassification | sign of the conditional estimate preserved, bias reported, false-positive rate not above the Type-I target | for confusion rates 10%, 20%, 30% |
| Computational cost | reported only; no pass/fail |  |

### D3. Scenarios (the ten requested, with generators and what each adds)

| # | Scenario | Generator (dependence envelope) | Measured | Notes / additions |
| --- | --- | --- | --- | --- |
| 1 | Complete null | trade R bounded by stop/target geometry (not only normal), plus heavy-tailed gaps | Type-I, FWER, CI coverage | baseline; also run with 0 trades in many months |
| 2 | Drift without skill | price drift ± at 3 levels, persistent regimes; signals random in time, side fixed (always long / always short) and mixed | false "skill", false "economic edge" separately | the engine's no-skill baseline R must be measured first; an always-long strategy is **not** a zero-mean-R null \[V\] — define the null as "no information beyond the passive benchmark" |
| 3 | General edge | true μ ∈ {0.1, 0.2, 0.3, 0.5}R in every regime | power, MDE, interval coverage |  |
| 4 | Conditional edge | μ > 0 only in bullish (or bearish / high-vol) state, zero or negative elsewhere; edge size × regime share grid | power for Q1, Q2, Q3 separately; false conditional label rate when the edge is general | include the case "edge is general but looks conditional by chance" |
| 5 | Persistent regimes | Markov chain with mean durations 3, 6, 12, 24 months; month-level AR(1) φ ∈ {0, 0.5, 0.8}; trade-level AR ∈ {0, 0.3, 0.7} | all error rates vs K | number of independent episodes recorded |
| 6 | Unequal activity | trades per month from Poisson/negative-binomial with 0–30% empty months and 5× imbalance; edge correlated or uncorrelated with activity | estimand definition, bias, size | estimand (per trade vs per calendar month) compared head to head |
| 7 | Volatility clustering | regime-dependent and AR(0.8) volatility; R scaled by volatility | size, power | include stop distance in ATR units to match the engine |
| 8 | Multiple search | M = 100, 500, 2,000 strategy/config/regime combinations; 90–99% null; neighbouring configurations correlated (ρ = 0.5–0.95); shared market path | FWER, FDR, power per true effect | pipeline = discovery in DEV → freeze → test in VALID, not the test alone |
| 9 | Regime misclassification | confusion rates 10/20/30%, errors concentrated at regime boundaries, label lag 0–5 bars | bias of conditional estimate, false-positive rate | include a classifier whose errors are correlated with the strategy's own signals |
| 10 | Selection bias | pick best (strategy, regime, parameters) in DEV; test in VALID with the *same pipeline* | post-selection Type-I, winner's-curse bias of DEV estimate, calibration of VALID p | the selection rule is written down; compare with a pipeline without selection |
| 11 | **Edge decay (added)** | μ(t) decays or switches off after freeze | detection time, false "confirmed" rate on a vanished edge | tests prospective tier |
| 12 | **Cost misspecification (added)** | true costs 1–2× modelled | sign of the verdict |  |
| 13 | **Repeated research cycles (added)** | 5–20 cycles each modifying strategies after exposure to the same validation set | cumulative false-confirmation rate with and without an alpha ledger | shows the cost of quiet reuse |

### D4. Sample-size and power investigations

Quantities to tabulate, each with a simulation-based curve **and** the analytic approximation, so a mismatch is visible:

- &#91;T\] Required effective trades for MDE μ: N ≈ ((zα + zβ)·σ/μ)² · DE. With σ = 1.5R: 0.10R needs 1,400 / 2,300 / 3,400 trades at α = 0.05 / 0.01 / 0.00125; 0.20R needs a quarter of that; 0.50R about 130 at 0.00125 — which is why the audit's oracle MDE at 120 trades is ≈ 0.5R \[V\]. σ must be replaced by the measured trade sd of each strategy; the 1.5 is the audit generator's value.
- A grid over K ∈ {24, 36, 60, 120} months × trades per month {2, 5, 10} × DE ∈ {1, 2, 4, 8} → MDE surface, and the **number of active months** and **independent regime episodes** alongside the number of trades.
- Regime share f ∈ {1/3, 1/2}: conditional MDE ≈ general MDE / √f at best \[T\]; with episode persistence the binding constraint becomes the number of episodes (≥ \~10 are needed for any episode-level test to have more than a coarse p-value \[T\]).
- The cost of multiplicity: m ∈ {1, 3, 10, 82}; Holm level 0.10/m.
- Simulation counts needed to *verify* the targets \[T\]: a per-test rate at 0.00125 to within ±30% needs \~35,000 datasets (±15%: \~140,000); an FWER near 0.10 to ±0.01 needs \~3,500 independent families; interval coverage of 0.95 to ±0.005 needs \~7,300. Tails below 0.00125 are not resolved at feasible counts and are not claimed.

### D5. Decision rule at the end of the program

If no estimator meets D2 across the envelope with usable power, the framework does not adopt one: it adopts **"not testable at this sample"** as a legitimate verdict and moves the burden to the prospective tier or to a longer window in a future protocol. That outcome is acceptable; an optimistic compromise is not.

## E. Conditional strategy protocol \[P\]

Applies to any rule that is claimed to work only in a declared state: bullish, bearish, high volatility, ranging, breakout. The state is part of the strategy, not a post-hoc description of when it happened to work.

### E1. Steps, in order

1. **Declare (before any DEV run for this strategy).** Signal rule and direction; regime variable and states drawn from the frozen taxonomy; the exact causal definition (inputs only from completed bars, thresholds absolute or expanding-window, evaluation time = the bar close at which the order is placed); the operating boundary in one sentence ("long XAUUSD D1 only while the regime reads bullish"); the primary claim class (general or conditional, economic or skill); the cost scenario; the estimand; the minimum economic effect that would matter.
2. **Feasibility (Q4), without strategy returns.** From the frozen design compute expected trades in the regime, active months, independent regime episodes and the resulting MDE under the dependence envelope. Episode *rates* are estimated on DEV prices; counting episodes on VALID or HOLD prices would be a look at protected data and is **not** done without your separate permission. If the MDE exceeds the declared minimum effect, the strategy is registered as "not testable at the confirmatory tier" and goes to the prospective tier or is dropped — it is not run on VALID hoping for luck.
3. **DEV exploration.** Variants allowed, each counted; any change of regime definition after seeing results creates a *new* strategy with a new registration and counts in the family. DEV yields candidates, never classes.
4. **Freeze.** Hash the strategy, regime definition, thresholds, estimand, cost scenario, classification target and analysis plan. The hash goes into the registry. Anything changed afterwards is a new strategy; the validation set it touched is exposed for the old one.
5. **Confirmation on VALID, once.** Gatekeeping order Q1 → Q3 → Q2 inside the filtered strategy; each gate uses its own null and is not combined with the others:
   - G1 (economic): lower bound of the conservative interval for the *filtered* strategy ≥ declared minimum after stressed costs.
   - G2 (filter value): paired filtered-minus-unfiltered monthly difference interval above zero. This is the interaction test; it replaces the "bullish +0.25R vs bearish −0.05R" comparison, which is a comparison of two noisy numbers chosen after the fact.
   - G3 (skill): excess over the regime-matched passive benchmark, with direction, timing and regime-selection reported separately.
   - G4 (robustness, descriptive, no p): sign and rough size preserved under the pre-registered secondary classifier and under simulated label noise at 10–30%.
6. **Classify** by the table below. A gate that is not reached because an earlier one failed is "not evaluated", not "passed".
7. **Operate within the boundary and monitor.** Live use only when the classifier says "on"; the same causal classifier runs forward; regime-drift or edge-decay monitors feed the prospective tier. Performance outside the boundary is not part of the claim and is reported descriptively only.

### E2. Classification

| Class | Required gates | Not allowed |
| --- | --- | --- |
| 2 Conditional economic edge | G1 on the filtered strategy; regime frozen before VALID; feasibility passed | claim of skill; extension of the boundary; promotion to Class 1 |
| 4 Conditional predictive skill | Class 2 + G2 + G3 (regime-matched benchmark, not the market-wide control) | awarding G3 from a market-wide control; using the best-looking regime after the fact |
| 1 General economic edge | G1 on the *unfiltered* strategy; no declared regime significantly negative at the family level | deriving Class 1 from a conditional strategy because "it also works elsewhere" |
| 3 Predictive skill | Class 1 + G3 | — |
| 5a Rejected | interval excludes the declared minimum effect | — |
| 5b Inconclusive — insufficient power | MDE of the design > claimed effect, interval contains 0 and the minimum | being reported as failure or as promise |

A long-only strategy in a bullish regime that matches "always long in that regime" can be Class 2 (the economic edge is real and tradable) and is *not* Class 4; the report says in one line that it is equivalent to passive exposure within the filter.

### E3. Handling repeated research cycles

&#91;P\] A ledger in the registry records every exposure of VALID by strategy hash, date and gate outcome. A modified strategy cannot be confirmed on a VALID window that has produced results for any ancestor (the existing `derived_from` rule already encodes this for v1.2). For a new cycle the options are: (a) a fresh window (prospective data), (b) the same window with an explicit alpha-spending ledger across cycles (cost: shrinking power), (c) none — the candidate stays "Inconclusive". Silent reuse is not an option.

## F. Compatibility with protocol v1.2 \[P\]

**Short answer:** the calibration program and the design review coexist with v1.2 untouched. Almost nothing that changes how a strategy is *judged* can be added to v1.2 without amending it; those parts need a separate protocol version or a separate research branch.

| Component | Under v1.2 as locked? | What it needs |
| --- | --- | --- |
| Synthetic calibration program (D) | Yes — no market data, no registry, no production file | audit branch only; same no-touch log |
| Feasibility/MDE computation (Q4) on frozen designs | Yes, if run on DEV prices or synthetic only | additional *report* fields; no threshold changes |
| Reporting intervals, power curve and MDE next to the existing gates | Yes as descriptive output | the v1.2 gates remain the pass/fail rule |
| Replacing the monthly-bootstrap significance gate, the family definition, or the control gate | **No** | protocol v1.3 or v2 — these are locked thresholds and definitions |
| Regime filter as part of the strategy; regime variants counted in the 82-family | **No** | the 82-family and the 15 registered hypotheses are fixed; regime variants would be new hypotheses → a new registry or an amendment with fingerprint change |
| Five-class (or six-class with 5a/5b) classification | **No** (v1.2 has pass/fail/UNPROVEN statuses) | new protocol; could map onto UNPROVEN subtypes |
| Evidence ledger across research cycles | partly: `derived_from` already exists | extension of registry event types |
| Prospective (post-freeze) evidence tier | **No** | new protocol decision; also needs an operational source of fresh data |
| Matched-control redefinition (regime-matched passive benchmark, separate direction/timing/regime nulls) | **No** | new protocol; existing control gate stays as locked |

**Data-allocation conflict to decide before anything touches VALID.** \[T\] VALID and HOLD have 0 trials and 0 HOLD accesses today. If v1.2 spends VALID on the 15 registered hypotheses and a later framework also wants VALID for conditional variants of the same strategies, the second use is a re-use of the same data: its multiplicity must be counted against the first. Recommendation: decide *now* which protocol owns VALID and HOLD for which hypotheses; do not run both on the same windows as if each were fresh.

**Options (decision is yours):**

1. **v1.2 unchanged, v2 as a separate research branch with its own registry** that may share DEV data but not claim confirmatory status on VALID/HOLD already earmarked for v1.2. Lowest risk to the lock; slowest.
2. **Amend to v1.3** (change of fingerprint, new lock) once the calibration program passes or declares "not testable"; v1.2's untouched VALID/HOLD can then be used under the stronger rules. Cleanest for evidence, but changes the locked protocol — a decision with its own review.
3. **Run v1.2 as-is and label its VALID outcomes "uncalibrated gate"** (the audit's conclusion). Not recommended as the confirmatory standard.

None of these is implemented, selected or implied by this review.

## G. Explicit limitations

Even if every synthetic calibration test passes, the framework still **cannot**:

1. **Prove that a real edge exists.** Calibration shows error rates under *assumed* generators; it says nothing about whether a given strategy has an edge. A confirmed strategy is evidence of an edge at a stated error level, not proof.
2. **Establish that the real dependence lies inside the simulated envelope.** The dependence of real strategy returns (regime persistence, volatility clustering, tails, structure breaks) is unknown and cannot be measured on VALID/HOLD without consuming them. Every guarantee is conditional on the envelope.
3. **Provide power for modest edges at the available sample.** \[T\] A true +0.10R edge needs on the order of 1,400–3,400 effective trades at confirmatory levels. If the design cannot supply that, the correct output is "inconclusive", and the framework will say so for most realistic strategies.
4. **Rule out regime-selection bias completely.** Freezing before VALID controls the selection *within* the pipeline; it does not remove the researcher's prior knowledge of what has worked in gold since 2018, which shaped the very taxonomy (bullish/bearish/volatility). The calibration of Scenario 10 measures the pipeline, not the researcher.
5. **Guarantee the future.** Edges decay and regimes change (Scenario 11); a confirmed result is retrospective evidence plus whatever the prospective tier adds.
6. **Separate skill from market structure in all cases.** Matched controls address drift and exposure; a strategy that exploits a persistent structural feature (e.g., gold's trend persistence) is indistinguishable from skill if the benchmark also contains that feature. Whether "exploiting persistence" counts as skill is a definition to be fixed, not a result.
7. **Make D1/H4 XAUUSD and EURUSD independent confirmations.** They share the USD factor; the two instruments and two timeframes are correlated draws, not four experiments.
8. **Cover execution reality.** Demo-server data, modelled costs, no queue/slippage dynamics, assumed 7 USD/lot commission, weekend and news gaps — the economic edge is conditional on the cost model.
9. **Replace judgement about economic meaning.** The declared minimum effect and the error-rate targets are decisions, not statistical facts; a bad choice is not detected by any test.
10. **Be trusted before being verified.** Everything tagged \[T\] or \[P\] in this document is unmeasured. In particular the conditional-edge power, interaction tests and misclassification behaviour have **never been simulated**; I do not know whether the proposed design will meet the targets, and if it does not, the honest outcome is a smaller claim, not a looser target.

**Unfavourable findings I did not hide:** my own audit shows the current monthly gate is not a controlled test; block bootstraps made it worse; the most robust test I found has almost no power; and a conditional claim needs more data than the unconditional one. This review does not offer a way around those facts.
