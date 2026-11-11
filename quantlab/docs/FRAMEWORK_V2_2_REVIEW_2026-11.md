# QuantLab Framework V2.2 — Independent Methodological Resolution

Nov 11, 2026 · @Ameer

## A. الملخص التنفيذي

**الخلاصة: لا يوجد اليوم أي اختبار D أو T أو S معتمد. الاختبارات الثلاثة بصيغتها في V2.1 غير معتمدة (Uncertified)، ولا يجوز استخدام أي منها كبوابة قرار. وثيقة مراجعة وتصميم فقط: لا كود، لا محاكاة جديدة، لا DEV/VALID/HOLD، لا تعديل على v1.2 أو PR #5 أو أي دمج.**

الوسوم: **\[V\]** قيس فعلاً في تدقيق سابق (بيانات تركيبية فقط)، **\[T\]** اشتقاق نظري أو حساب حسابي مباشر، **\[P\]** اقتراح لم يُنفَّذ أو يُختبر. أي ادعاء عن الأدبيات (Ibragimov–Müller، Dufour، Müller، Howard–Ramdas وغيرهم) مذكور من الذاكرة ولم يُتحقق منه، وهو موسوم \[T\] مع هذا التنبيه.

**1. ماذا وجدت في كل اختبار**

- **D (مهارة الاتجاه):** Sign-flip الشهري في V2.1 صالح فقط إذا كان الاتجاه «عملة عادلة» مستقلة عن النتيجة. لذلك يختبر «هل الاتجاه الفعلي أفضل من اتجاه عشوائي متوازن»، وليس «هل للاتجاه مهارة». عند وجود drift مع انحياز جانبي (مثلاً 70% شراء في سوق صاعد) يرفض الاختبار الفرضية الصفرية دون أي مهارة \[T\]. الصيغة الصحيحة نظرياً هي التباين المشترك بين الاتجاه والنتيجة نسبةً إلى خط أساس معلن، وتحتاج صفقات غير متداخلة وبنية Martingale Difference.
- **T (مهارة التوقيت):** الإزاحة الدائرية لأوقات الإشارات دقيقة تماماً فقط إذا كانت الإشارات خارجية (جدول أحداث، فتح جلسة) ومستقلة عن مسار السعر. في breakout وmomentum تُشتق الإشارة من السعر نفسه، فيكسر الإزاحةَ ارتباطُ وقت الإشارة بالتقلب وبحالة السعر \[T\]. وسبق أن عُويرت الإزاحة لإحصاءة الحدث فقط، لا لأرباح الاستراتيجية \[V\].
- **S (اختيار النظام):** إزاحة التصنيف تحافظ على duty cycle وطول الحلقات، لكنها تفترض أن التصنيف مستقل عن السعر والتقلب والتكلفة. هذه فرضية أقوى بكثير من «لا مهارة». وإحصاءة S في V2.1 هي عملياً إحصاءة قيمة الفلتر (قيمة الفلتر = −π\_out)، فهي لا تفصل المهارة عن القيمة الاقتصادية \[T\].

**2. التصنيف.** D وT وS: Uncertified. طرق الاستدلال الموجودة قيست في تدقيق سابق، ولا طريقة منها اجتازت الغلاف الكامل \[V\]. الطريقة الوحيدة التي صلاحيتها نظرية (Confidence Sequences) تبقى مشروطة بافتراضات (حد خسارة معلن، ملاحظات شهرية مغلقة، حدود متنبَّأ بها) وتحتاج معايرة تنفيذها قبل الاعتماد. وE\_core لا تمنح شهادة عامة تحت أي ظرف (القسم C).

**3. ما يمكن إثباته وما لا يمكن.**

- يمكن (نظرياً، بشروط): ادعاء اقتصادي عن R/month، أو عن قيمة مضافة نسبةً إلى خط أساس معلن، عبر Confidence Sequences على ملاحظات شهرية مغلقة \[T\].
- لا يمكن بعينة تقل عن 5 سنوات وأداة واحدة: مهارة التوقيت أو مهارة اختيار النظام بمستويات تأكيدية. الدقة الدنيا لاختبارات الإزاحة والتبديل مرتبطة بعدد الحلقات الفعلية لا بعدد الصفقات: لبلوغ p ≈ 0.00125 نحتاج نحو 12 حلقة مستقلة على الأقل، وهذا أفضل حالة \[T\].
- لا يمكن إطلاقاً من داخل استراتيجية واحدة مشتقة من السعر: فصل «الاتجاه» عن «التوقيت» عن «النظام»، لأنها دوال للمعلومات نفسها \[T\].

**4. القدرة والمدة** (σ = √2 R للصفقة كما في مولّد التدقيق، 5 صفقات/شهر، قدرة 80%، استقلال تام) \[T\]:

- **+0.10R للصفقة** (0.5R/شهر): نحو 20.6 سنة عند α = 0.05، و33.5 سنة عند 0.01، و49.8 سنة عند 0.00125. مع اعتماد زمني متوسط (DE = 4) تتضاعف المدة أربع مرات: 82 إلى 199 سنة. **غير قابل للإثبات عملياً.**
- +0.30R للصفقة: 2.3 إلى 5.5 سنة. +0.50R: 0.8 إلى 2.0 سنة.
- هذه حدود دنيا متفائلة: التباين معلوم فيها، بينما تقديراته من 24 شهراً منحازة للأسفل بين 15% و75% تحت الاستمرارية \[V\].

**5. تصحيحات على V2.1 نفسها** (التفاصيل في القسم I): (أ) sign-flip في D لا يعزل المهارة عن drift؛ (ب) إحصاءة S هي إحصاءة قيمة الفلتر؛ (ج) صلاحية الإزاحة في T لم تكن مثبتة للإشارات المشتقة من السعر؛ (د) بروتوكول تجاوز حد الخسارة ونمط القص غير المتماثل لم يكونا مذكورين في وصف Confidence Sequences؛ (هـ) هدف Confidence Sequences هو متوسط التوقعات الشرطية وليس «الأفضلية غير المشروطة».

**6. القرارات الستة تبقى بيدك:** الحد الأدنى لـ R/month، تاريخ نهاية HOLD، حجم عائلة التأكيد، غلاف المعايرة النهائي، اعتماد أي اختبار، وبناء التنفيذ الظلي. توصياتي وأسبابها في القسم H فقط، ولم أتخذ أياً منها.

## B. Validity review of D, T and S

**None of the three reference distributions proposed in V2.1 is valid as stated.** Each is valid only under an independence or exchangeability condition that trade streams from price-derived rules generally violate. Nothing below is adopted; each subsection fixes a null, lists the assumptions that would make a method valid, and says what a rejection would and would not mean. All statements are \[T\] unless tagged otherwise.

### B.0 Notation, and the two nulls V2.1 conflated

Month m = 1..K. Trade i is entered at t\_i with direction d\_i in {-1, +1} (known at entry, F\_{t\_i}-measurable). Y\_i is the long-side outcome in R units under the strategy's own exit rule, gross of cost; c\_i is the realised cost in R. The net outcome is R\_i = d\_i Y\_i - c\_i. Let m\_i = E\[Y\_i | F\_{t\_i-}\] be the conditional drift of the long side.

```latex
H_0^{econ}:\ \bar{E}[R_i \mid F_{t_i-}] \le 0 \qquad\qquad H_0^{skill\text{-}D}:\ \bar{E}[(d_i - b_i)\, m_i] = 0
```

The economic null asks whether the rule makes money. The skill null asks whether the direction d\_i adds anything beyond a declared, predictable baseline b\_i (for example constant long, or the sign of the trailing return). They coincide only when the baseline is a fair coin (b\_i = 0) and there is no drift. With drift and side imbalance they differ, and that gap is where V2.1's D test breaks.

### B.1 D: direction skill

**1. Mathematical null.** V2.1's monthly sign-flip takes D\_m = sum over trades in month m of d\_i Y\_i (gross directional P&L) and treats the 2^K sign patterns of (D\_1..D\_K) as the null distribution. That is a valid reference only for the symmetry null:

```latex
(D_1,\dots,D_K) \overset{d}{=} (\epsilon_1 D_1,\dots,\epsilon_K D_K)\quad \forall\, \epsilon \in \{\pm 1\}^K
```

This holds when D\_m = sigma\_m \* e\_m with e\_m i.i.d. symmetric and sigma\_m predetermined (arbitrary heteroskedasticity is allowed). It also holds exactly when d\_i is a fair coin independent of Y\_i, which is the randomised-direction null. It is not the null "d has no skill".

**2. Why it is not the skill null.** Let d\_i be independent of Y\_i, with E\[Y\_i\] = mu (drift) and P(d\_i = +1) = p. Then E\[d\_i Y\_i\] = mu (2p - 1). With p = 0.7 this is 0.4 mu, non-zero with zero skill. The sign-flip rejects with probability tending to 1 as K grows, while the thing detected is drift capture through side imbalance. That is a real economic effect, but it is H0^econ, not H0^skill-D. V2.1's label "direction skill" for this test is withdrawn.

**3. Assumptions the sign-flip would need.**

- A1. Mirror symmetry: the reversed trade pays exactly the negative of the actual trade. This fails with costs (both sides pay), with asymmetric brackets (a reversed 1R-stop / 3R-target trade does not stop where the original targeted), and with gaps.
- A2. Conditional symmetry of D\_m about zero given the other months' magnitudes. Skewed monthly P&L, or a sign correlated with past magnitude (leverage effect), breaks it.
- A3. Independence across months, or a martingale-difference structure with conditional symmetry.
- A4. No selection on activity: empty months carry no information under any sign, so the effective K is the number of active months.

**4. Cases where it is invalid.**

- Drift with side imbalance (above).
- Serial dependence. Flipping signs independently destroys sign persistence, so the reference variance is sum of D\_m squared while the true variance is inflated by the design effect DE = (1 + rho)/(1 - rho) for AR(1) months. Asymptotically a nominal one-sided test at level alpha rejects at Phi-bar(z\_alpha / sqrt(DE)) \[T\]:

| Month AR rho (DE) | nominal 0.05 | nominal 0.01 | nominal 0.00125 |
| --- | --- | --- | --- |
| 0.5 (3) | 0.171 (3.4x) | 0.090 (9.0x) | 0.040 (32x) |
| 0.8 (9) | 0.292 (5.8x) | 0.219 (21.9x) | 0.157 (125x) |

- These are asymptotic figures \[T\]. The earlier audit measured the analogous t-test in the dependence set at 3.8 to 47.3x for level 0.00125 \[V\], the same order of magnitude. The sign-flip itself was never run in the audit, so no empirical claim is made about it.
- Overlapping trades and positions carried across month ends make D\_m dependent even when the underlying innovations are not. Exit-time assignment reduces this and does not remove it.
- Unequal or zero trade counts: in the gap study at K = 24, level 0.00125, no dependence, the production procedure over-rejected by 4.1x (G2, 30% empty months), 5.1x (G6, dense negative-binomial counts) and 8.9x (G10, 60% empty months) \[V\]. Any equal-weight monthly resampling inherits this.
- Direction depends on price or regime (momentum sign, trend filter). The direction is then a function of the same path that generates Y, so the fair-coin interpretation fails, and any persistent drift that the regime carries is reported as direction skill.

**5. Alternatives, with their own nulls and limits.**

| Method | Null it tests | Valid when | Invalid or weak when |
| --- | --- | --- | --- |
| Covariance permutation within strata (stratum = month x declared covariate bin) | d independent of Y given the stratum | d exchangeable within stratum; strata contain everything driving both d and Y | Y serially dependent or overlapping; d is a deterministic function of past prices (no real assignment randomness) |
| Martingale / confidence-sequence contrast X\_i = (d\_i - b\_i) Y\_i with predictable baseline b\_i | average conditional expected value of d over b is zero | observations bounded, closed (fully realised) and predictably ordered, i.e. non-overlapping or exit-time indexed | baseline not predictable (for example the sample mean of d); bound breached; claim read as "skill" instead of "value over baseline" |
| Circular shift of d against Y | the d series is independent of the Y series | stationarity, long series, many effectively distinct shifts | price-derived d (see B.2); stronger null than "no skill" |
| Explicit counterfactual: simulate the reversed trade with its own exits and costs, then use paired monthly differences | reversed trade is no better than actual | Counterfactual is faithfully executable | Inference step still needs a dependence-valid method (not the sign-flip) |

**6. What can and cannot be proven.**

- Provable (second row, if A holds): the average conditional expected gain of the direction rule over a pre-declared baseline is at least delta, uniformly over time. This is **value over baseline**, not covariance skill, and its target is the average of conditional means (section E).
- Not provable: that d "predicts" independent of drift or regime persistence. The conditional drift m\_i is unobservable, so any information the baseline omits and d uses is indistinguishable from skill. This is an identification limit, not a sample-size limit.
- Sample size, sign test, i.i.d., non-overlapping trades \[T\]: a hit rate of 55% needs about 616 trades at alpha 0.05 and 1,491 at 0.00125 (10.3 and 24.8 years at 5 trades per month). A hit rate of 60% needs 152 and 370 trades (2.5 and 6.2 years). A hit rate of 52% needs 3,862 and 9,333 trades (64 and 156 years).

### B.2 T: timing skill

**1. Mathematical null.** Let tau be the set of entry times, d the directions, and Y\_t the outcome of a trade entered at t. The timing statistic is Theta(tau) = sum over t in tau of d\_t Y\_t. V2.1's circular shift tests the invariance null:

```latex
(\tau \oplus k,\; Y) \overset{d}{=} (\tau,\; Y)\quad \forall k, \qquad \tau \oplus k = \{(t + k) \bmod T : t \in \tau\}
```

It reads: the pattern of signal times, rotated by any offset, is as good as the actual pattern. That is a statement about the joint law of the signal-time process and the outcome process. It is exact when (a) tau is independent of Y and (b) Y is invariant under circular shifts (stationary, wrap-around negligible).

**2. Assumptions.**

- T1. Exogenous timing: tau does not depend on the price path (calendar, session open, scheduled events, an external model with no price input).
- T2. Stationary outcome process, series long relative to its dependence length.
- T3. Shifts larger than the holding period and the mixing length, and enough effectively distinct shifts to reach the target level (resolution, below).
- T4. Trade geometry (entry price, stop and target distances, size) and the cost state are recomputed at the shifted time. Carrying the original geometry to a different bar mixes stale levels with unrelated prices.
- T5. Where signals are tied to sessions or weekdays, shifts are restricted to multiples of the seasonal period. Otherwise the shift also changes the intraday or weekday alignment, and the null is stronger than intended.

**3. Cases where it is invalid.**

- **Signals derived from prices (breakout, momentum).** tau is a function of the path, so tau is not independent of Y. A breakout at an n-bar extreme coincides with a volatility expansion. Under a pure martingale price, the expected gross R of a symmetric bracket is still zero, but the variance of R and the cost-to-stop ratio depend on local volatility, which differs at signal times and at shifted times. The reference mean and variance are then wrong in a direction that depends on the strategy and cannot be known in advance.
- **Momentum.** d\_t = sign of the trailing return, Y\_t is the forward outcome. Under the martingale null the shift is acceptable for the mean, but volatility clustering distorts the variance, and the alternative "returns are autocorrelated" is exactly the generating relation that a shift of the signals severs. This is T and D at once.
- **Drift with side imbalance.** The shift preserves the imbalance and meets the same drift, so it is correctly centred here. This is its advantage over the sign-flip.
- **Non-stationarity.** Calm-period signals shifted into a crisis (or the reverse) give a null spread that is too narrow or too wide, with no fixed sign of the error.
- **Resolution.** The number of effectively distinct shifts is about T / l, with l the larger of signal spacing, holding period and volatility persistence length. For roughly 1,300 D1 bars (five years) and l of 20 to 60 bars, that is 20 to 65 distinct shifts, so the smallest attainable p-value is about 0.015 to 0.05. The level 0.00125 cannot be reached by a shift test on five years of single-instrument data \[T\].
- **Measured scope \[V\].** In the earlier audit the circular-shift reference was calibrated for the event statistic only, not for strategy P&L.

**4. Alternatives.**

| Method | Null | Valid when | Limits |
| --- | --- | --- | --- |
| Regenerate-and-rerun surrogate prices: simulate paths from a declared null model M0 (martingale or AR with volatility clustering), recompute signals, exits and costs end to end | prices follow M0 | M0 is adequate for the features the strategy trades on (tails, clustering, gaps, intraday seasonality) | Misspecified M0 gives unknown-direction error. It tests the whole strategy against M0 and cannot isolate timing |
| Matched random timing: draw control entry times with the same count and the same distribution over declared covariates (volatility decile, session, regime, month); recompute geometry | timing carries no information beyond the declared covariates | conditional independence of timing given the strata; a large eligible pool | Wrong or missing covariates leave leakage. Earlier audit \[V\]: the matched-control p was calibrated at the 0.10 gate but rank-correlated only 0.53 to 0.83 with the bootstrap p, and no-skill drift strategies passed both gates 1.3% to 3.0% of the time |
| Design-based randomisation: in a pre-registered shadow run, randomise entry delay (for example plus or minus k bars) | entry timing has no effect on outcome | randomisation is real and trades do not interfere | Needs a shadow run; changes strategy fidelity; accumulates at the same slow rate of trades \[P\] |
| Confidence-sequence contrast against a predictable matched-time baseline | average value of signal time over control time is zero | bounded closed observations; control chosen from past information only | Estimand is value over a declared control, not timing skill in the abstract |

**5. What can and cannot be proven.**

- Provable for exogenous timing: whether the signal times beat rotated copies of themselves, up to the resolution limit above.
- Provable for price-derived timing: only that the strategy beats surrogate paths from M0, or beats matched random timing given declared covariates. Both are conditional statements.
- Not provable: that timing is separately skilful in a breakout or momentum strategy. Direction and entry time are both functions of the same lookback return r. Writing R = sign(r) Y with event e = {|r| at least c}, the expected R is a single quantity over the joint choice (sign, time). The two counterfactuals, "actual direction at random times" and "random direction at actual times", give different and order-dependent attributions, and there is no unique decomposition. Claiming timing skill separately from direction skill for such rules would be false precision.

### B.3 S: regime selection skill

**1. Mathematical null.** Let L\_t in {in, out} be a causal regime label, pi\_in the sum of R over trades entered while in, n\_in their count, N the total trades, and Z\_i declared covariates (volatility bucket, cost-to-stop ratio, side, session). Two different nulls are in play:

```latex
H_0^{S,cond}:\ E[R_i \mid L(t_i), Z_i] = E[R_i \mid Z_i] \qquad\qquad H_0^{S,shift}:\ (L \oplus k,\; R) \overset{d}{=} (L,\; R)
```

The first says the label carries no information about R once the covariates are fixed, which is what "regime selection skill" means. The second, which V2.1's circular shift tests, says the label process is distributionally independent of the whole outcome process, including volatility, costs and trade counts. The second implies the first and is much stronger, so rejecting it does not imply skill.

**2. Two defects of the V2.1 statistic.**

- **It is the filter-value statistic.** Filtered P&L is pi\_in, unfiltered is pi\_in + pi\_out, so the filter changes P&L by exactly -pi\_out. The V2.1 S test therefore measures filter economic value, not selection skill.
- **Composition mismatch.** Under the shift the in-regime trade count n\_in(k) varies, and the null expectation of pi\_in is mu \* n\_in(k), with mu the unconditional per-trade mean. The observed n\_in belongs to the actual labels. If the strategy simply trades more often in the labelled regime (a trend rule in a trend label) and mu > 0, then pi\_in is larger because n\_in is larger, and the test rejects with no selection skill. A composition-adjusted statistic fixes the mean:

```latex
\hat\Delta = \frac{\pi_{in}}{n_{in}} - \frac{\pi_{out}}{n_{out}} \quad (E_0[\hat\Delta] = 0\ \text{for any}\ \mu\ \text{and any}\ n_{in})
```

It removes the mean problem. It does not remove the dependence of the variance on counts, nor the label-to-volatility link.

**3. Assumptions a valid S test would need.**

- S1. The label process is stationary and independent of the outcome process, including volatility and cost (for the shift null), or the conditional null holds with Z fine enough to absorb the dependence.
- S2. The effective sample is the number of regime episodes E, not the number of trades.
- S3. Labels use only information available at entry. Any look-ahead in the label creates apparent skill.
- S4. Both states occur with non-trivial duty cycle in every analysed period.

**4. Cases where it is invalid.**

- **Label tied to volatility, trend or returns.** A volatility label predicts future |Y| mechanically. With a fixed cost, cost in R is c / stop distance and moves with volatility, so net R differs across regimes even with zero directional information. That is genuine filter value (the strategy should avoid expensive states) but it is not prediction of the market. The shift severs this link, so its null is too strong and it rejects for non-skill reasons.
- **Trend-label with a trend strategy.** In-regime trades have positive drift by construction, because the label is built from the persistence the strategy trades. S then duplicates D and T.
- **Non-stationary duty cycle.** If the share of "in" labels drifts across years, the wrap-around and the shifted copies are not comparable.
- **Misclassification and detection delay.** Random label noise attenuates the contrast and lowers power. It does not inflate size, so it makes failures to reject uninformative.
- **Resolution.** With E independent episodes, a sign test cannot go below 2^-E, and a balanced permutation of episodes cannot go below 1 / C(E, E/2) \[T\]:

| Episodes E | Sign-test floor 2^-E | Balanced permutation floor | Mean episode length for E = 60 months / L |
| --- | --- | --- | --- |
| 6 | 0.0156 | 0.050 | L = 10 months |
| 8 | 0.0039 | 0.0143 | L = 7.5 months |
| 10 | 0.00098 | 0.0040 | L = 6 months |
| 12 | 0.00024 | 0.0011 | L = 5 months |
| 14 | 0.00006 | 0.00029 | L about 4.3 months |

Reaching level 0.00125 therefore needs at least 12 balanced, independent episodes, which is the best case. Sixty months with a three-month typical episode gives about 20 episodes (10 in, 10 out), but episodes of the same state are not exchangeable (eras differ in drift and volatility), so the floors above are not attained.

**5. Controls that keep duty cycle and episode length.** None of them removes the independence assumption. They differ only in how they approximate the label process.

| Control | Preserves | Assumes | Main risk |
| --- | --- | --- | --- |
| Circular shift of labels | duty cycle, episode lengths and order exactly | joint stationarity; independence of label and outcome processes | null too strong when the label is tied to volatility or cost; few distinct shifts |
| Permutation of whole episodes (blocks) | multiset of episode lengths, duty cycle | episodes exchangeable | seasonality, eras and Markov dependence between successive episodes |
| Markov or semi-Markov label surrogate | fitted duty cycle and duration law | the fitted label model | gives many draws, but their validity is the validity of the model; heavy-tailed durations are distorted |
| Stratified contrast on declared covariates Z (volatility bucket, cost ratio, side) | covariate-conditional comparison | Z fine enough to absorb the label-to-covariate link | effective sample shrinks; temporal dependence remains and needs a martingale or block method |
| Regenerate-and-rerun surrogates with labels recomputed | the label-to-price relation | adequacy of the null price model M0 | tests label plus strategy against M0, not selection skill alone |
| Randomised filter on calendar blocks (filter ON or OFF assigned at random in a shadow run) | design-based validity | block-level randomisation, no interference | very few blocks, so very low power; needs a shadow run \[P\] |

**6. What can and cannot be proven.**

- Provable (confidence sequence over monthly outcomes): filter economic value, that is, that out-of-regime trades lose at least x R per month. This is an economic claim and it is monotone in the out-of-regime trades.
- Not provable: that the label "selects" or "predicts". Even a correct test of the per-trade contrast is \[T\] at least sqrt(1/f + 1/(1-f)) times harder than a one-sample test of the same sample: 2.0x for a half-time regime, 2.1x for one third, 2.5x for one fifth, 3.3x for one tenth. At 60 months and level 0.00125 the one-sample MDE is about 0.32R per trade (section F), so a half-time regime contrast needs a difference near 0.64R per trade. A single instrument over five years does not support a confirmatory selection-skill claim.

## C. Methods, assumptions and the certification classes

**Every D, T and S method in B is Uncertified today. The only methods with any measured calibration are the monthly mean-inference procedures from the earlier audit, and none of them passed the full envelope.** This section fixes what each certification class permits, tabulates the existing measurements, and states how E\_core is to be treated.

### C.1 The three classes

| Class | Evidence required | May claim | May not claim |
| --- | --- | --- | --- |
| **Certified over full envelope** | Upper 95% confidence bound of (actual rejection / nominal) at most 1.5 in every cell of the full declared envelope, at levels 0.05, 0.01 and 0.00125, for every K in the declared grid; power reported separately | "If the data-generating process lies in the declared envelope, the false-claim rate is at most about 1.5 times nominal." Gate use in the registry | Anything about processes outside the envelope; that the envelope is the real market; that an edge exists or will persist; that skill was proven (the estimand limits that) |
| **Certified under restricted assumptions** | Same criterion, but only on a named sub-envelope, or a proof under written assumptions A plus a calibration of the implementation under A | "Valid if A holds." Reported with the assumption list and the excluded scenarios, and labelled conditional | Unconditional wording ("significant", "proven"); use outside the named scope; treating an assumption as satisfied because it could not be checked; use as a registry gate for a general claim |
| **Uncertified** | No demonstrated size control, or the method's null is not the claim's null | Descriptive statistics, exploratory ranking, hypothesis generation, with the label "non-inferential" | Any pass/fail gate, the word "significant", any registry entry stating evidence |

Promotion needs the pre-registered calibration in section D, passed as written. A change of thresholds after seeing results resets the class to Uncertified. A method that is calibrated but has near-zero power at the planned K (as below for IM-4) is certified and useless; the power statement must accompany the class.

### C.2 What the earlier audit measured \[V\]

Synthetic data only, 13 scenarios, 100,000 replications per cell, K = 24 and 60 months, levels 0.05, 0.01, 0.00125. Column 2 counts scenarios (of 13) in which the upper 95% bound of the size ratio is at most 1.5 at all three levels. The dependence set is S1, T3, M2, M3, M4.

| Method | Pass count K=24 / K=60 | Worst point ratio, dependence set K=24 / K=60 | Class (full envelope) |
| --- | --- | --- | --- |
| Production iid-month bootstrap | 3 / 7 | 56.0x / 53.3x | Uncertified |
| Circular block bootstrap (block 3) | worse than the iid bootstrap in 11/13 (K=24) and 8/13 (K=60) scenarios | 52.1x / 34.5x | Uncertified |
| t-test | 8 / 8 | 38.4x / 47.3x | Uncertified over full envelope. Passes the eight non-dependence scenarios: restricted scope possible, see C.3 |
| Newey-West lag 1 | 6 / 8 | 33.2x / 34.8x | Uncertified |
| Fixed-b | 9 / 10 | 9.5x / 5.0x | Uncertified |
| AR effective-sample-size | 8 / 9 | 23.7x / 23.2x | Uncertified |
| Ibragimov-Mueller, 4 groups (IM-4) | 10 / 12 | 2.5x / 1.6x (upper bounds 2.80x / 1.85x) | Uncertified over full envelope (fails the 1.5x criterion). Restricted scope possible, see C.3 |

The criterion "upper bound at most 1.5x in every envelope cell" is the V2.1 D2 criterion. No tested method meets it \[V\].

### C.3 Classification of every candidate relevant to D, T, S and the prospective tier

| Candidate | Class today | Reason | Declared restricted scope, if any | Path to promotion |
| --- | --- | --- | --- | --- |
| t-test on monthly means | Certified under restricted assumptions \[V\] | Passes at both K in all scenarios without month dependence (M1, N1, N2, T1, T2, V1, V2, V3); 38x to 47x over-rejection with dependence | Months independent, no persistence in monthly P&L. This assumption cannot be diagnosed from K = 24 to 60 months: the estimated variance from 24 months is biased low by 15% to 75% under persistence \[V\] | Cannot be promoted over the full envelope; keep descriptive |
| IM-4 | Certified under restricted assumptions \[V\] | K=24 passes all scenarios except M2, M3, M4; K=60 passes all except M3 | Excludes strong monthly persistence. Power at level 0.00125 for a 0.5R effect is only 8.6% (K=24) and 25.9% (K=60) \[V\], so the class is hollow for confirmatory use | None found: premise failure, adjacent 6-block means correlated 0.44 at AR 0.8 \[T\] |
| D: monthly sign-flip (V2.1) | Uncertified, **withdrawn** | Null is the fair-coin symmetry null, not the skill null (B.1); never calibrated | none | Replace with D-covariance or value-over-baseline CS |
| D: stratified covariance permutation | Uncertified | Never calibrated; needs exchangeable direction within strata | none yet | Scenarios 1 to 4, 8, 9, 11 in section D |
| T: circular shift of signals | Uncertified for strategy P\&L; Certified under restricted assumptions for the event statistic only \[V\] | Calibrated in the event study; not for P&L | Event-study statistic, exogenous timing | Scenarios 1 to 4, 7, 9 for P&L |
| T: regenerate-and-rerun surrogates, matched random timing | Uncertified | Matched-control p calibrated only at the 0.10 gate and correlated 0.53 to 0.83 with the bootstrap p \[V\]; no-skill drift strategies passed both gates 1.3% to 3.0% \[V\] | none | Scenarios 1 to 4, 7, 9, 14 |
| S: circular shift of labels (V2.1) | Uncertified, **withdrawn** | Statistic is filter value; composition mismatch (B.3) | none | Replace with per-trade contrast on covariates or surrogates |
| S: event-study S-mode sampler | Certified under restricted assumptions \[V\] | Calibrated for the event statistic | Event-study use only | Not extendable to trade P&L |
| Confidence sequences, bounded monthly observations | Uncertified (implementation not calibrated); theory conditional on A1 to A5 of section E | Validity is a theorem under bounded, closed, predictable observations; no calibration of an implementation with realistic gaps, costs, bound breaches yet | Bounded predictable observations; no bound breach | Scenarios 7, 8, 11 to 14 |

The two "restricted" rows for the t-test and IM-4 are classifications of what was measured. They are not recommendations to use either method. Both exclude exactly the dependence that real monthly strategy P&L is most likely to have, and the exclusion cannot be verified from the sample.

### C.4 E\_core is not the full envelope

- Passing in E\_core can earn at most "Certified under restricted assumptions: E\_core", and every report must carry the list of scenarios E\_core excludes.
- It may not be used to declare a general certification, to fill the "full envelope" field in the registry, or to support the word "certified" without that qualifier.
- The scenarios that broke every method in the audit (the dependence set) are the ones a reduced envelope is most tempted to drop. Dropping them to obtain a pass is the failure mode this rule exists to block.
- Shrinking the envelope after seeing which scenarios fail is a threshold change and resets the class (C.1).

### C.5 Assumption matrix

| Method | Months or units independent? | Stationarity? | Exchangeability needed | Generative model needed? | Bounded observations? | Assumption checkable in sample? |
| --- | --- | --- | --- | --- | --- | --- |
| Monthly sign-flip | yes | symmetry about zero | sign symmetry | no | no | no (mirror symmetry unobservable) |
| Stratified covariance permutation | within strata | mild | direction exchangeable within stratum | no | no | partly (covariate balance) |
| Circular shift (D, T or S) | the two series independent | yes, plus long series | shifts equivalent | no | no | weakly |
| Regenerate-and-rerun surrogate | implied by model | implied by model | none | **yes** (null price model) | no | partly (goodness of fit of the model) |
| Matched random timing | conditional on strata | mild | exchangeable within strata | no | no | covariate balance only |
| Episode permutation | episodes exchangeable | yes | episodes | no | no | no |
| Confidence sequence | none beyond martingale-difference structure | none | none | no | **yes**, predictable bounds | bound breaches are detectable after the fact; the closed-observation property is by design |

## D. Future calibration design (nothing here has been run)

**One scenario matrix covers D, T, S and the confidence-sequence tier. Every item is \[P\]: a proposal, not executed, with no result attributed to it.** Nothing runs until the envelope, the failure thresholds and the replication count are fixed by Ameer (decisions 4 and 5 in section H).

### D.1 Rules that apply to every scenario

- **Envelope.** 14 scenarios x K in {24, 36, 60, 120} months x trades per month n in {2, 5, 10, 20} x levels {0.05, 0.01, 0.00125}. Parameter grids are written into the registry before any run. No parameter is tuned after seeing a result.
- **Replications.** For a rate near 0.00125, a truly nominal test passes an upper-bound criterion of 1.5x with probability about 30% at 10,000 replications, 55% at 20,000, 88% at 40,000 and 99% at 80,000 \[T, exact binomial / Clopper-Pearson arithmetic\]. So 80,000 per cell at the strictest level; fewer is noise, not calibration.
- **Failure forms.** (F-size) the upper 95% bound of rejection rate / nominal exceeds 1.5 in any cell of the test's declared scope. (F-power) power at the declared minimum effect is below the declared floor (proposal: 80%); the test is then labelled "cannot test this size", not "fails". (F-coverage) for confidence sequences, the probability that the target ever leaves the interval exceeds 1.5 x alpha. (F-breach) the realised rate of declared-bound breaches exceeds the declared tolerance. (F-misattribution) a skill test rejects in a scenario where its own null is true, whichever other skill is present: this is a size failure of that test.
- **Negative controls.** Several cells are built so that a named method must fail (marked NC). If it does not fail, the scenario is not doing its job and is redesigned before anything else is read.
- **Reporting.** All cells are published, including failures, with the seeds. Failed cells are not re-run under a different seed.

### D.2 Scenario matrix

| # | Scenario (what is simulated) | Tests exercised | Counts as calibration failure |
| --- | --- | --- | --- |
| 1 | **True null, no skill, no drift.** i.i.d. R; variants normal, heavy-tailed, and a bracket payoff (stop 1R, target 2R, hit probability 1/3) | D (all variants), T, S, CS, economic test | F-size in any cell; CS coverage below 1 - 1.5 alpha |
| 2 | **Drift without predictive skill.** Price drift mu\_p > 0; side imbalance p in {0.5, 0.7, 0.9}; direction independent of the outcome | D sign-flip (NC), D covariance permutation, D value-over-baseline CS, T shift, S per-trade contrast, S V2.1 statistic (NC) | Any skill test rejecting beyond 1.5 alpha. NC methods that fail to reject: the scenario is mis-specified |
| 3 | **True direction skill.** Hit rate 0.52, 0.55, 0.60 with random timing; with and without drift | D variants; T and S must not reject | F-power at the planned (K, n); T or S rejecting (their null is true) |
| 4 | **True timing skill.** (a) entries placed before volatility or drift bursts with random direction; (b) informative direction at random times; (c) both | T, D, crossed | T power below floor in (a); D rejecting in (a) or T rejecting in (b): F-misattribution |
| 5 | **Persistent regime.** Two-state Markov latent regime, duty cycle {0.3, 0.5, 0.7}, mean episode {1, 3, 6, 12} months, regime-dependent drift; (a) labels independent of the latent regime, (b) labels equal to it | S (every control in B.3), D | F-size in (a); in (b) F-power, and smallest attainable p above alpha at that episode count E ("cannot test") |
| 6 | **Abruptly changing regime.** A structural break at a random month in drift, volatility or edge; edge decaying to zero or flipping sign | CS cumulative and windowed monitor; shift and permutation tests under a null with a break | Decay not flagged within the declared delay; F-size for shift and permutation under the null with a break |
| 7 | **Volatility clustering.** GARCH(1,1) persistence 0.90, 0.95, 0.98; leverage on and off; null mean zero; adaptive bounds from ATR | All tests; CS with adaptive bounds | F-size; CS coverage; F-breach for the ATR-based bound |
| 8 | **Dependence between months.** Monthly AR(1) rho in {0.3, 0.5, 0.8}, common shocks, trade-level AR {0.3, 0.7}, streaks (the audit's dependence set S1, T3, M2, M3, M4) | All tests | F-size. This scenario removed every method in the earlier audit \[V\] and may not be dropped from the envelope |
| 9 | **Price-derived signals.** Simulated prices (a) random walk, (b) random walk with GARCH, (c) random walk with drift, (d) AR(1) returns phi 0.05 to 0.10 (true predictability); Donchian breakout and n-bar momentum; stops, targets, costs recomputed | T shift (NC in a to c), T surrogate, matched random timing, D, S with volatility or trend labels | F-size in (a) to (c) for any test used to claim skill; F-power in (d) |
| 10 | **Regime misclassification.** Labels equal the latent regime with random error {0.1, 0.3, 0.5} and detection lag {0, 10%, 30%} of the episode | S | Any size inflation; power below floor is reported as "label uninformative", not as no skill |
| 11 | **Overlapping trades.** Holding period vs entry spacing giving overlap fraction {0, 25, 50, 80}%; positions carried across month ends | Trade-level, exit-time monthly and thinned analyses; CS indexed by trade (NC) and by month | F-size for the declared unit of analysis; the trade-indexed CS must fail (NC) |
| 12 | **Unequal trade counts.** n\_m Poisson or negative binomial; 0% to 60% empty months; counts that depend on past P&L | Monthly resampling weights, R per month vs R per trade, S composition adjustment, CS with variable n\_m | F-size (the audit saw 4.1x to 8.9x with the production procedure at K=24 \[V\]); CS coverage failing when counts are predictable |
| 13 | **Cost and slippage change.** Cost shift {0.02, 0.05, 0.10} R at a random month; volatility-dependent costs; gap losses beyond the declared bound at rate {0, 0.2%, 1%}; backtest cost vs realised cost | CS with bound L, R per month claim, net vs gross D, T, S definitions | CS coverage below target; breach protocol (section E) not triggered within the declared delay; a net claim that does not reverse when the stress is at least the claimed effect |
| 14 | **Selecting the best of a family.** m in {1, 3, 5, 10, 82} strategies with no skill (with and without drift); best chosen on DEV-type data, confirmed on fresh data; naive selection on the same data as the control | Holm, Bonferroni alpha-ledger, e-value procedures; CS union spending | Family-wise error above 1.5 x the declared family level; winner's-curse bias of the selected effect estimate above tolerance. Reference \[V\]: Holm with the production p gave family-wise error 0.146, 0.592, 0.728 and 0.997 (no dependence; trade AR 0.7; month AR 0.5; month AR 0.8) |

### D.3 What passing would and would not show

- A pass shows that a method holds its size inside the declared envelope on synthetic data. It does not show that the real market lies in the envelope, that an edge exists, or that a skill has been proven.
- A pass on a sub-envelope earns the restricted class, never the full one (C.1, C.4).
- Scenarios 3, 4 and 5(b) measure only whether a skill of a stated size would be detectable at a stated sample size. Failing them does not mean the skill is absent. It means the claim is untestable at that size, which is itself a result to report.

## E. Confidence sequences: independent mathematical review

**A confidence sequence (CS) is the only candidate in this document whose validity is a theorem rather than a calibration, but the theorem needs conditions that real execution can break, it answers a narrower question than V2.1's wording implied, and it is not more powerful than a fixed-sample test.** All statements are \[T\]. The literature behind them (Howard, Ramdas, McAuliffe and Sekhon 2021; Waudby-Smith and Ramdas; Wang and Ramdas) is recalled from memory and not re-verified for this document.

### E.1 What is guaranteed

Observations X\_t are monthly net R (calendar month, exit-time assignment, open positions marked at month end, empty month recorded as 0). F\_t is the information at month t. Bounds \[-L\_t, U\_t\] are fixed using F\_{t-1} and must contain X\_t almost surely. The target is the running average of conditional means:

```latex
\bar\mu_t = \frac{1}{t}\sum_{s=1}^{t} E[X_s \mid F_{s-1}], \qquad P(\forall t \ge 1:\ \bar\mu_t \ge \ell_t) \ge 1 - \alpha
```

The guarantee holds simultaneously over all t, so looking at every month and stopping when a claim passes does not inflate the error. Two family members matter: sub-Gaussian / empirical-Bernstein boundaries, which cover the running average of conditional means directly, and betting constructions, which are tight for a constant mean. Whether a betting construction extends cleanly to time-varying conditional means must be checked before use \[recalled, not verified\].

**The target is not the unconditional edge.** Under monthly persistence the conditional mean moves with the past (for AR(0.8) it is 0.8 times last month's P&L). The average of conditional means differs from the unconditional mean by a zero-mean term of order sigma / sqrt(t) that cannot be bounded without stationarity and ergodicity. So the claim that is certified is "the strategy's expected monthly R, given its own history, averaged about delta over the observed months". It is a statement about what was earned in expectation over the sample, not about the future.

### E.2 Conditions for validity

- **A1. Closed observations.** Each X\_t is fully realised and recorded at month end. The unit is the month, never the trade: with overlapping trades, trade i is still open when trade i+1 is entered, so trade-indexed increments are not martingale differences.
- **A2. Almost-sure, predictable bounds.** L\_t and U\_t depend only on the past, and X\_t lies inside them always, not usually.
- **A3. Predictable bets and weights.** Betting fractions, mixing priors, baselines b\_t are chosen from the past only.
- **A4. Pre-declared claim.** Direction, threshold delta, level alpha and the target (running average of conditional means) are fixed before data. Changing delta or the sign after looking is a new claim and spends new alpha.
- **A5. No selective omission.** A month cannot be removed after the fact. Empty months enter as zero.
- **A6. Observation is the realised P&L.** Costs, slippage and swaps are inside X\_t.

### E.2b Power cost of the bound (continuation of E.2)

- **Range-based (Hoeffding-type) CS.** Needs about W^2 ln(1/alpha) / (2 mu^2) observations to bring the width to mu, with W = L + U. For a per-trade range of 4R (-1R to +3R) and mu = 0.10R, that is 2,397 trades at alpha 0.05, before the time-uniform inflation (roughly 1.5x to 2x), against 1,237 trades for a fixed-sample 80%-power test. At monthly level the a.s. range is up to n times larger (20R for 5 trades), which is n times worse: 2,397 months, about 200 years. **Range-based CS at monthly level is unusable.**
- **Variance-adaptive CS (empirical Bernstein, betting).** With the true variance and an optimal bet, expected observations are about 2 ln(1/alpha) sigma^2 / mu^2: 1,198 / 1,842 / 2,674 trades for mu = 0.10R at alpha 0.05 / 0.01 / 0.00125, against 1,237 / 2,007 / 2,988 for the fixed-sample test. This oracle figure is a floor; real bets are estimated and cost more \[P, unquantified\].
- **The bound can cap the bet.** Bets must satisfy lambda < 1 / (L\_t + m) so wealth stays positive. For a 0.5R per month target with sigma^2 = 10 (5 trades, sigma^2 = 2 each), the optimal bet is 0.05 and the growth rate 0.0125 per month. A declared monthly loss bound of 50R caps the bet at 0.02 and the growth rate at 0.0080, 64% of the optimum, so about 1.56 times more months. Declaring a gap-safe bound is not free.

### E.3 If the actual loss exceeds the declared bound

- A breach removes the almost-sure premise. The supermartingale property fails at that step, so the guarantee is lost for the sequence from then on, and for any claim that uses the breached month. If the bound held only with probability 1 - eta, the guarantee degrades to at least 1 - alpha - eta, and eta cannot be estimated from a few years of a fat-tailed series.
- **Clipping is asymmetric.** Capping wins at U gives a clipped mean at most the true mean, so a lower CS on it stays conservative for an edge claim: allowed. Flooring losses at -L gives a clipped mean at least the true mean, so the lower CS then overstates the edge: **forbidden**. A breach cannot be repaired by clipping the loss.
- **Proposed protocol \[P\].** (1) Pre-register the bounds and their justification. (2) Declare a breach whenever realised X\_t < -L\_t. (3) On a breach, freeze all claims that use that month, record the true loss, and mark the ledger "assumption violated". (4) Do not enlarge L retroactively and pool: a bound chosen after seeing X is not predictable. Start a fresh CS from the next month with a larger declared L, spending from a reserved alpha, and keep the old months as archive, not pooled. (5) A claim issued before the breach stands as issued, labelled with its date.
- A heavy-tail alternative (Catoni-type CS, finite variance only) removes the almost-sure bound but needs a known variance bound and has larger constants \[recalled\]. It trades one assumption for another.

### E.4 Gaps, slippage and variable costs

- **Gaps.** A gap can take the loss beyond the stop distance, so L must come from the worst plausible gap and from the broker's execution terms, not from the largest loss in the backtest. A historical maximum is a lower bound on the true maximum.
- **Slippage and variable cost.** They are acceptable if realised and recorded in X\_t, and if L covers the worst case including cost. A backtest cost model is an assumption: the CS then speaks for the strategy at the assumed cost c. At cost c + d per trade, the monthly mean falls by n d, for example 0.25R per month for d = 0.05R at 5 trades \[T\]. Claims must be written "net of cost model c" with that stress line.
- **Costs correlated with losses.** Larger stop slippage on losing trades is fine if realised. It is not fine if an assumed cost ignores it.

### E.5 Adaptive bounds without voiding the guarantee

- **Allowed:** bounds, bets, mixing parameters and baselines that are F\_{t-1}-measurable, as long as the a.s. containment holds. Tightening predictable bounds as evidence accrues is fine going forward.
- **Not allowed:** anything chosen after seeing X\_t, or retroactive re-bounding.
- **ATR-based bounds** (L\_t = k x ATR\_{t-1}) are probabilistic unless the loss is mechanically capped (hard stop with guaranteed fill, time stop, size cap). A probabilistic bound turns the guarantee into 1 - alpha - P(breach).

### E.6 Distribution shift and strategy decay

- The CS stays valid under non-stationarity because its target is an average. That is also its weakness: an edge of 0.5R per month for 36 months followed by zero leaves a running average of 0.25R per month after 72 months, so the cumulative lower bound can stay above delta long after the current edge is gone.
- A **windowed monitor** (CS or e-process on the last W months, pre-registered W and alpha\_mon, with a suspend rule) is a separate tool. At 5 trades per month the monthly standard deviation is about 3.2R, so over W = 12 months the standard error is 0.91R per month \[T\]. Erosion of a 0.5R-per-month edge is undetectable in that window. The monitor protects against collapse, not against erosion.

### E.7 Multiplicity across parallel strategies

- **Alpha ledger (Bonferroni).** Weights alpha\_j with sum at most alpha, pre-registered, with a reserve (for example 20%) for strategies added later. Valid under arbitrary dependence. Ignores correlation between strategies, so it is conservative. Cost of larger families: section F.6.
- **e-value procedures.** Each strategy's wealth process is an e-process for its null. Bonferroni on e-values (reject when E\_j reaches m / alpha) controls family-wise error; e-BH controls false discovery rate under arbitrary dependence \[recalled, not verified\].
- **The family is all strategies started,** not the survivors. A strategy published after looking at which one is ahead must be charged to the whole started family.
- **Fixed-sequence gatekeeping** (a pre-registered order, a later test only if the earlier one passes) spares alpha for later tests, at the price of an order that cannot be changed.

### E.8 Comparison with alternatives

| Method | Validity basis | Dependence | Optional stopping | Needs bounds | Power relative to fixed-sample test | Not automatically better because |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed-sample t / bootstrap at a pre-registered N | asymptotic | fails: 3.8x to 56x over-rejection with dependence at K = 24 to 60 \[V\] | no | no | reference | invalid under the dependence set |
| IM-4 | asymptotic, group means near independent | partial: 2.5x / 1.6x worst \[V\] | no | no | 8.6% / 25.9% power at 0.00125 for 0.5R \[V\] | fails the 1.5x criterion and is almost powerless |
| Group-sequential (O'Brien-Fleming, Pocock) with a HAC statistic | asymptotic normality | not guaranteed | limited number of looks | no | near fixed-sample | inherits HAC size problems \[V\] |
| Range-based CS | exact | by construction (martingale target) | yes | yes | about 2x to 4x worse per trade; n times worse monthly | width set by the worst case |
| Variance-adaptive CS | exact | by construction | yes | yes | oracle floor 1,198 vs 1,237 trades; real cost higher \[P\] | bound breach voids it; cap on bet; target is average conditional mean |
| Bayesian posterior | prior-dependent | model-dependent | yes | no | depends on prior | error control depends on prior calibration; no frequentist guarantee |
| Design-based randomisation in a shadow run | randomisation | by design | yes | no | low (few blocks) | needs a shadow run and real randomisation \[P\] |

### E.9 Verdict

CS is the right object for a prospective, economic, dependence-robust claim, with these limits: observations monthly and closed; almost-sure bounds with a breach protocol; variance-adaptive form only; target stated as average conditional expected R per month; claims net of a stated cost model; no future-performance reading. Before adoption its implementation must pass the scenarios of section D marked for CS (1, 6, 7, 8, 11, 12, 13, 14). Whether to adopt it is decision 5 in section H.

## F. Power, minimum detectable effect and duration

**A +0.10R per-trade edge is not provable in a human time frame at confirmatory levels with about 5 trades per month (about half the time at 10): about 21 years at level 0.05 and about 50 years at level 0.00125 under full independence, and four times that under moderate monthly dependence.** Edges of 0.3R to 0.5R per trade are provable in roughly 1 to 6 years under the same optimistic assumptions. Every number in this section is \[T\] arithmetic from the formula below. No simulation was run.

### F.1 Assumptions (all optimistic)

```latex
MDE = (z_{\alpha} + z_{\beta})\,\sigma\,\sqrt{\frac{DE}{n\,K\,f}}
```

- sigma = sqrt(2) R per trade, the standard deviation of the earlier audit's generator \[V as a parameter\]. MDE scales linearly with sigma; years scale with sigma squared.
- n = 5 non-overlapping trades per month (duration tables also show n = 20); K months; f the share of trades that survive a regime filter (f = 1 for a general strategy).
- One-sided test, power 80% (z\_beta = 0.842), levels 0.05, 0.01, 0.00125 (z = 1.645, 2.326, 3.023).
- The variance is known. In practice it is estimated, and the audit found variance estimates from 24 months biased low by 15% to 75% under persistence \[V\]. Real power is lower than shown.
- **Trades are not independent observations.** DE (design effect) divides the effective sample. For AR(1) months, DE is about (1 + rho) / (1 - rho) asymptotically: 2 for rho = 0.33, 4 for rho = 0.6, 9 for rho = 0.8. For within-month clustering with intra-month correlation kappa it is 1 + (n - 1) kappa: 2 for n = 5, kappa = 0.25. DE = 1 means every trade is an independent draw, which is not assumed to be true, only shown as the best case.

### F.2 General strategies: MDE in R per trade (n = 5)

| K (months) | DE | level 0.05 | level 0.01 | level 0.00125 |
| --- | --- | --- | --- | --- |
| 24 | 1 | 0.32 | 0.41 | 0.50 |
| 24 | 2 | 0.45 | 0.58 | 0.71 |
| 24 | 4 | 0.64 | 0.82 | 1.00 |
| 36 | 1 | 0.26 | 0.33 | 0.41 |
| 36 | 2 | 0.37 | 0.47 | 0.58 |
| 36 | 4 | 0.52 | 0.67 | 0.81 |
| 60 | 1 | 0.20 | 0.26 | 0.32 |
| 60 | 2 | 0.29 | 0.37 | 0.45 |
| 60 | 4 | 0.41 | 0.52 | 0.63 |
| 120 | 1 | 0.14 | 0.18 | 0.22 |
| 120 | 2 | 0.20 | 0.26 | 0.32 |
| 120 | 4 | 0.29 | 0.37 | 0.45 |

The K = 24 and K = 60 cells at DE = 1 and level 0.00125 (0.50R and 0.32R) match the oracle MDE80 measured in the earlier audit \[V\]. In R per month, multiply by n = 5: the 60-month cell at 0.00125 is 1.6R per month at DE = 1 and 3.2R per month at DE = 4.

### F.3 Conditional strategies (trades only inside a regime)

A filter that keeps the fraction f of trades leaves n f trades per month, so the MDE per in-regime trade is the general MDE divided by sqrt(f). Levels 0.05 and 0.00125 (R per in-regime trade):

| K | DE | general 0.05 / 0.00125 | f = 1/2 | f = 1/3 |
| --- | --- | --- | --- | --- |
| 24 | 1 | 0.32 / 0.50 | 0.45 / 0.71 | 0.56 / 0.86 |
| 24 | 4 | 0.64 / 1.00 | 0.91 / 1.41 | 1.11 / 1.73 |
| 36 | 1 | 0.26 / 0.41 | 0.37 / 0.58 | 0.45 / 0.71 |
| 36 | 4 | 0.52 / 0.81 | 0.74 / 1.15 | 0.91 / 1.41 |
| 60 | 1 | 0.20 / 0.32 | 0.29 / 0.45 | 0.35 / 0.55 |
| 60 | 4 | 0.41 / 0.63 | 0.57 / 0.89 | 0.70 / 1.09 |
| 120 | 1 | 0.14 / 0.22 | 0.20 / 0.32 | 0.25 / 0.39 |
| 120 | 4 | 0.29 / 0.45 | 0.41 / 0.63 | 0.50 / 0.77 |

**A skill contrast is harder than an economic test.** Comparing in-regime with out-of-regime per-trade means has an MDE of sqrt(1/f + 1/(1 - f)) times the general MDE: 2.0x at f = 1/2, 2.1x at 1/3, 2.5x at 1/5, 3.3x at 1/10. At 60 months, DE = 1, level 0.00125, a half-time regime needs a per-trade difference of about 0.64R (0.32R x 2). Direction skill measured by hit rate is in B.1 (55% accuracy: about 10 and 25 years at 5 trades per month).

### F.4 Years needed to prove a given edge (DE = 1 and DE = 4)

Trades needed at DE = 1: mu = 0.10R needs 1,237 / 2,007 / 2,988 trades at levels 0.05 / 0.01 / 0.00125; 0.20R needs 309 / 502 / 747; 0.30R needs 137 / 223 / 332; 0.50R needs 49 / 80 / 120. Years = trades x DE / (12 n).

| Edge per trade | n = 5, DE = 1 (0.05 / 0.00125) | n = 5, DE = 4 (0.05 / 0.00125) | n = 20, DE = 1 | n = 20, DE = 4 |
| --- | --- | --- | --- | --- |
| 0.10R | 20.6 / 49.8 years | 82 / 199 years | 5.2 / 12.4 years | 20.6 / 49.8 years |
| 0.20R | 5.2 / 12.4 | 20.6 / 49.8 | 1.3 / 3.1 | 5.2 / 12.4 |
| 0.30R | 2.3 / 5.5 | 9.2 / 22.1 | 0.6 / 1.4 | 2.3 / 5.5 |
| 0.50R | 0.8 / 2.0 | 3.3 / 8.0 | 0.2 / 0.5 | 0.8 / 2.0 |

### F.5 What size is provable within 10, 20 or 50 years

Smallest edge per trade with 80% power:

| Setting | 10 years | 20 years | 50 years |
| --- | --- | --- | --- |
| n = 5, DE = 1, level 0.05 | 0.144R | 0.102R | 0.064R |
| n = 5, DE = 1, level 0.00125 | 0.223R | 0.158R | 0.100R |
| n = 5, DE = 4, level 0.05 | 0.287R | 0.203R | 0.128R |
| n = 5, DE = 4, level 0.00125 | 0.446R | 0.316R | 0.200R |
| n = 20, DE = 1, level 0.05 | 0.072R | 0.051R | 0.032R |
| n = 20, DE = 1, level 0.00125 | 0.112R | 0.079R | 0.050R |
| n = 20, DE = 4, level 0.00125 | 0.223R | 0.158R | 0.100R |

### F.6 Cost of a larger confirmation family

With a family-wise level of 0.10 split equally (alpha = 0.10 / m), trades and years at n = 5, DE = 1, 80% power:

| Family size m | per-test alpha | 0.10R: trades (years) | 0.20R | 0.30R | 0.50R |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1 | 902 (15.0) | 225 (3.8) | 100 (1.7) | 36 (0.6) |
| 3 | 0.033 | 1,432 (23.9) | 358 (6.0) | 159 (2.7) | 57 (1.0) |
| 5 | 0.02 | 1,677 (28.0) | 419 (7.0) | 186 (3.1) | 67 (1.1) |
| 10 | 0.01 | 2,007 (33.5) | 502 (8.4) | 223 (3.7) | 80 (1.3) |
| 82 | 0.0012 | 2,999 (50.0) | 750 (12.5) | 333 (5.6) | 120 (2.0) |

### F.7 Is +0.10R per trade practically provable?

**No, not at confirmatory levels, with the data we can plausibly have.**

- At 60 months and 5 trades per month there are about 300 trades and a standard error of 0.082R (1.414 / sqrt(300)) at best. An observed +0.10R is about 1.2 standard errors from zero. It can be estimated, with an uncertainty wider than the effect, but not established.
- Sizes that need about 10 years: 0.14R to 0.22R. About 20 years: 0.10R to 0.16R. About 50 years: 0.064R to 0.10R. Under moderate monthly dependence (DE = 4) double those values.
- Only a much higher trade rate changes the picture: 20 independent non-overlapping trades per month brings 0.10R to about 5 years at level 0.05 and 12 years at level 0.00125, and requires a rule that genuinely trades that often without overlap.
- The HOLD window cannot confirm small effects either. If HOLD is about 22 months (January 2025 to October 2026, assuming the data reach October 2026, not verified), the general MDE at level 0.00125 is about 0.52R per trade at DE = 1 and about 1.04R at DE = 4.
- The confidence-sequence floor (E.2b) is not better than these fixed-sample numbers. At best it matches them with the true variance.

## G. Identity of economic and skill claims

**A strategy can be profitable with no predictive skill at all, and a profitable result is never evidence that the indicator or filter predicts the market.** The six claims below are different statements with different estimands and different evidence. A registry entry must name exactly one of them. The word "edge" without a qualifier is not used, and "predicts" is reserved for claims 3 to 5. All statements are \[T\] unless tagged.

### G.1 The six claims

| # | Claim | Formal estimand | Evidence that could establish it | What it does not show | Testable with our data? |
| --- | --- | --- | --- | --- | --- |
| 1 | **General Economic Edge** | Average monthly net R of the strategy as traded, at a named cost model, at least delta (average conditional expected R per month, section E) | Confidence sequence on closed monthly net R, bounded, with a breach protocol; or a fixed-sample test inside its restricted scope | That direction, timing or regime is predictable; that the edge persists; that it is independent of drift | Only for large delta: about 0.3R to 0.5R per trade within 1 to 6 years, 0.10R not provable (F) |
| 2 | **Conditional Economic Edge** | Same, for a condition declared in advance (regime, session, side); months outside the condition count as zero | Confidence sequence on the conditional strategy's monthly P&L | That the condition selects well; that a condition defined after looking at results is anything but a post-hoc subset | Harder by 1 / sqrt(f) per in-condition trade (F.3) |
| 3 | **Predictive Direction Skill** | Average of (d\_i - b\_i) m\_i is positive for a declared predictable baseline b\_i, where m\_i is the conditional drift; with constant b, the covariance of direction and outcome | Stratified covariance permutation under conditional exchangeability; or a confidence sequence for value over the baseline (weaker: value, not covariance) | Profit: skill can be real and still lose money after costs. Also not independent of drift or regime persistence the baseline omits | Hit rate 55% needs about 10 to 25 years at 5 trades per month; 52% is out of reach (B.1) |
| 4 | **Predictive Timing Skill** | Entry times carry information about outcomes beyond declared covariates | Shift for exogenous timing; matched random timing given covariates; randomised delay in a shadow run | Separate timing skill inside a breakout or momentum rule (no unique decomposition, B.2) | Resolution-limited: p below about 0.015 to 0.05 on five years of single-instrument data for shift tests |
| 5 | **Regime Selection Skill** | E\[R given label, covariates\] differs from E\[R given covariates\]; per-trade contrast between in and out | Stratified contrast on declared covariates; surrogate paths with labels recomputed | Filter economic value; that the label predicts rather than proxies volatility or cost | Not at confirmatory level with 60 months (contrast is 2.0x to 3.3x harder; episodes needed at least 12, B.3) |
| 6 | **Filter Economic Value** | Monthly R gained by applying the filter equals minus the out-of-regime monthly P&L, at least delta\_f | Confidence sequence on monthly out-of-regime P&L (or filtered minus unfiltered monthly P&L) for a filter fixed in advance | That the filter predicts anything; it may come from avoiding high-cost or low-volatility states, or from concentrating a general edge | Same order as claim 1 for the out-of-regime stream |

### G.2 What implies what

| If this is shown | Does it imply | Why |
| --- | --- | --- |
| General edge (1) | Predictive direction skill (3) | No. A long-only rule in a drifting market earns mu x (2p - 1) with zero covariance between direction and outcome |
| Direction skill (3) | General edge (1) | No. Predictability smaller than the cost per trade gives positive skill and negative net R |
| Filter value (6) | Regime selection skill (5) | No. The filter pays if out-of-regime trades lose, whatever the reason: costs relative to stop size, low volatility, or a general edge concentrated in one state |
| Regime selection skill (5) | Filter value (6) | No. A better per-trade mean in-regime can be too small, or come with too few trades, to raise monthly P&L after costs |
| Edge in the filtered stream (2) | The filter works | No. The unfiltered stream may earn more in total. Only claim 6 compares them |
| Timing skill (4) and direction skill (3), each shown separately | Edge (1) | No. Neither implies net profit, and neither is separately identifiable for price-derived rules |

### G.3 Profit without predictive skill

**Yes, it happens, and it can be a legitimate economic edge.** Four sources that involve no prediction:

- **Drift capture.** Long-only, or a long-biased rule, in an asset with positive drift: E\[R\] is positive, covariance with direction is zero.
- **Cost avoidance.** Skipping states where cost in R (cost / stop distance) is high. The filter pays without forecasting direction.
- **Payoff shape and risk premium.** Rules that sell convexity or carry a premium earn a positive mean with negative skew and no prediction.
- **Sizing and rebalancing effects.**

**When this is acceptable as an economic edge.** All of the following:

1. The claim is written as claim 1, 2 or 6, net of a named cost model, never as prediction.
2. The source is named (drift, carry, cost avoidance), with the baselines reported: constant-side exposure and random direction with the same side imbalance.
3. The evidence is a closed-observation confidence sequence with its bounds and breach protocol (section E).
4. No persistence outside the observed regime is asserted unless a structural reason is argued, and a decay monitor is in place (E.6).

**When it is not enough.**

- To say that an indicator, filter or signal "predicts" or "carries information". That needs claims 3 to 5, with baselines that remove drift, volatility and cost.
- To transfer the result to another instrument, period or regime.
- To stack several components on the assumption that each has skill.
- To attribute profit to a mechanism, or to justify a more complex model on the strength of a profitable simple one.
- To credit a filter after comparing filtered with unfiltered results in a sample in which the filter was chosen.

### G.4 Registry discipline \[P\]

Every entry carries one claim identity from the table, its estimand, its cost model and bounds (claims 1, 2, 6) or its baseline and covariates (claims 3 to 5), its evidence method, and its class from section C. An entry without these is descriptive and is labelled non-inferential.

## H. Open decisions and recommendations

**Six decisions remain open and belong to Ameer. Nothing in this document decides any of them, changes v1.2, PR #4 or PR #5, touches VALID or HOLD, or adopts a test. The right-hand columns are recommendations with reasons, to be accepted, changed or rejected.**

| # | Decision | Options | Recommendation (not a decision) | Reasons | What the choice changes |
| --- | --- | --- | --- | --- | --- |
| 1 | **Minimum economic effect, R per month** | (a) 0.5R per month (0.10R per trade at 5 trades); (b) about 1.5R per month (0.30R per trade); (c) about 2.5R per month (0.50R per trade) | Set it from the provability budget, not from ambition: consider the 1.5R to 2.5R per month range, write down the years it implies, and fix it before any DEV result. Treat edges below it as "unprovable", not "absent" | Option (a) needs about 21 to 50 years at DE = 1 and 82 to 199 at DE = 4 (F.4). Option (b) needs 2.3 to 5.5 years at DE = 1 and 9 to 22 at DE = 4. Option (c) needs 0.8 to 2.0 years and 3 to 8. A cost-stress margin of 0.05R per trade is already 0.25R per month \[T\] | The horizon of the prospective tier, the family budget, and which strategies are worth building |
| 2 | **HOLD end date** | Open-ended rolling; a fixed calendar date; a rule tied to power | Close HOLD by a rule fixed in advance (for example the first calendar quarter in which the feasibility ledger shows at least 80% power at the chosen minimum effect), not by a date chosen after results exist. Keep HOLD untouched until then | Closing HOLD when results look favourable is optional stopping of data collection. A HOLD of about 22 months (assumed, not verified) has a general MDE of about 0.52R per trade at level 0.00125 and DE = 1 (F.7), so a small minimum effect needs a longer window | How long a confirmatory sample accrues, and when v1.2 or v2 may look |
| 3 | **Confirmation family size** | m = 1, 3, 5, 10, 82 | A small family (1 to 3 strategies) with an alpha ledger and about 20% of alpha held in reserve for later additions | At 0.10R per trade, going from m = 3 to m = 10 raises the trades needed from 1,432 to 2,007 (+40%), and m = 82 needs 2,999 (F.6). The family counts every strategy started, not the survivors (E.7) | The cost of each claim and the alpha left for new ideas |
| 4 | **Final calibration envelope** | Full 14-scenario envelope; reduced E\_core; full envelope with restricted classes reported | Declare the full 14-scenario envelope (D.2), 80,000 replications per cell at the strictest level, the 1.5x criterion and an 80% power floor, and accept "restricted" where methods fail. Never shrink the envelope after results | The dependence scenario removed every tested method in the earlier audit \[V\]. A reduced envelope that omits it produces a pass that carries no information (C.4) | Which methods can ever earn a class, and what a class means |
| 5 | **Adoption of any statistical test** | Adopt none; adopt confidence sequences for economic claims after calibration; adopt D, T or S tests | Adopt no D, T or S test as inferential. Consider a variance-adaptive, monthly, bounded CS for claims 1, 2 and 6 only after scenarios 1, 6, 7, 8, 11, 12, 13 and 14 pass and an independent review confirms it. Keep t-test and IM-4 descriptive | Every D, T and S method is Uncertified; two were withdrawn (C.3). The CS has a theorem but an unverified implementation and a demanding assumption list (E.2) | Whether any gate exists at all, and what the registry may call "evidence" |
| 6 | **Building shadow execution** | Build now; write the specification only; defer | Write the logging specification now (signal time, intended and filled price, spread, slippage, gap flag, cost, regime label, code version hash) and do not build until decisions 1, 3 and 5 are made | Shadow data would supply realistic gap and cost bounds for E.4 and look-ahead-free prospective evidence, and would allow randomised-delay designs (B.2). It does not shorten the time to prove a small edge, because trades arrive at the same rate | Whether prospective evidence starts accruing, and whether design-based checks exist |

### H.1 Suggested order of decisions

1. Minimum effect (1), because it fixes the horizon.
2. Family size (3), because it fixes the alpha per claim.
3. HOLD rule (2), from the horizon and the family.
4. Calibration envelope (4), which does not depend on the market outcome.
5. Test adoption (5), only after calibration results and an independent review.
6. Shadow execution (6), after 1, 3 and 5.

Decisions 1 to 4 can all be made before any DEV result exists, which is the point: none of them should be influenced by how a strategy performs.

## I. Limitations, what cannot be proven, and corrections to V2.1

**Some skill claims cannot be tested reliably with our data, and this document says so rather than offering a test that looks scientific and gives false confidence.**

### I.1 What cannot be proven

- **Predictive timing skill and regime selection skill at confirmatory levels, from about five years of single-instrument data.** The resolution of shift and permutation tests is limited by the number of effectively distinct shifts or episodes, and a contrast needs 2.0x to 3.3x the sample of an economic test (B.2, B.3, F.3). Not a weakness of a particular test: an information limit.
- **Timing, direction and regime as separate skills inside a breakout or momentum rule.** They are functions of the same information. Any decomposition depends on the order of the counterfactuals (B.2).
- **Direction skill independent of drift.** The conditional drift is unobservable, so skill versus regime persistence the baseline omits is an identification question, not a sample-size question (B.1).
- **A +0.10R per-trade edge,** at confirmatory levels and 5 to 10 trades per month (F.7).
- **That monthly dependence is absent.** It cannot be diagnosed from 24 to 60 months: variance estimates from 24 months are biased low by 15% to 75% under persistence \[V\], and impossibility results for inference on means under unrestricted dependence (Dufour; Mueller) are recalled, not re-verified.
- **Future performance.** A confidence sequence certifies the average conditional expected R over the observed months. Stationarity, which would turn it into a forecast, is not testable here.
- **Anything about the real market from the synthetic audit.** The audit and the proposed calibration use synthetic data. A pass is evidence about the envelope, not about gold or EURUSD.

### I.2 Corrections to V2.1

| # | V2.1 content | Correction in V2.2 | Where |
| --- | --- | --- | --- |
| 1 | D: monthly sign-flip used to test direction skill | It tests the fair-coin symmetry null. With drift and side imbalance it rejects with no skill. Withdrawn; replaced by covariance or value-over-baseline estimands | B.1 |
| 2 | T: circular shift of signals as the timing reference | Exact only for exogenous signals. For price-derived signals the generating relation is not preserved. Calibrated for the event statistic only \[V\] | B.2 |
| 3 | S: circular shift of regime labels, statistic pi\_in | The statistic is the filter-value statistic (minus pi\_out) and suffers composition mismatch. Withdrawn; per-trade contrast on covariates or surrogates | B.3 |
| 4 | "Certified" used with an envelope and a core | Three classes with stated permissions and prohibitions. E\_core cannot confer a general class | C.1, C.4 |
| 5 | Confidence sequences with a declared loss bound | Conditions A1 to A6; breach protocol; asymmetric clipping; target is the average of conditional means; range-based CS unusable monthly; the bound can cap the bet | E |
| 6 | MDE estimates | Re-derived at 24, 36, 60 and 120 months with design effects and conditional strategies; trades are not independent observations | F |
| 7 | Skill claims and economic claims treated alike | Six distinct claim identities, with implications that do not hold | G |

### I.3 Verification notes

- **Source of numbers.** Section C.2 pass counts were derived by re-reading the earlier audit's size table (columns for rejection rate, ratio, and the 95% upper bound of the ratio): counted scenarios whose upper bound is at most 1.5 at all three levels. That is a re-reading of measured data, not a new simulation. Section F values are closed-form arithmetic from the formula in F.1 and were cross-checked against the audit's oracle MDE80 (0.50R at K = 24 and 0.32R at K = 60, level 0.00125) and against the trade counts 1,237, 2,007 and 2,988 for 0.10R.
- **Grids not in the audit.** K = 36 and K = 120, and n other than 5 in the duration tables, are formula extensions, not measurements.
- **An intermediate error caught while drafting.** A first arithmetic pass for the duration and "edge reachable" tables used the significance level in place of its z-value and gave values inconsistent with the audit. Those outputs were discarded, never entered any document, and every table in F was recomputed and checked against the audit figures above.
- **Literature.** Statements about Ibragimov and Mueller (2010), Dufour (1997), Mueller (2014), Howard, Ramdas, McAuliffe and Sekhon (2021), Waudby-Smith and Ramdas, Wang and Ramdas, and e-BH are recalled from memory and not re-verified. They are used only to name known results, and none of the conclusions depends on a figure taken from them.
- **The validity claims in B are derivations,** not proofs about our data. A method is described as valid only under the listed assumptions, and none of those assumptions has been shown to hold for our strategies.
- **No new simulation, code, DEV, VALID or HOLD access, and no change to v1.2, PR #4, PR #5 or any production file was part of this document.**
