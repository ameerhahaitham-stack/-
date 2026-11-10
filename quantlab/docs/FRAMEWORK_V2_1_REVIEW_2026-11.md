# QuantLab Statistical Framework v2.1 — Final Review and Design

Nov 10, 2026 · Author: Claude (independent design review for Ameer) · Review and design only: no code, no project change, no market data, no new simulation. Supersedes nothing: V2 is kept; errata to V2 are in §1.

## الخلاصة بالعربية

هذه وثيقة مراجعة وتصميم فقط: لا كود، لا محاكاة جديدة، لا DEV أو VALID أو HOLD، لا تعديل على v1.2 أو PR #5. الوسوم: \[V\] مُثبت في تدقيقاتي الاصطناعية، \[T\] نظري أو حسابي، \[P\] مقترح لم يُنفّذ.

1. **تعارض D2 مع Ibragimov–Müller:** التعارض حقيقي. الحد الأعلى لـ IM-4 يصل 2.80× عند K=24 (الخلية M3) و 1.85× عند K=60، ولم تحقق أي طريقة من المختبرة المعيار في كل الخلايا. السبب هو فشل الفرضية (ارتباط الكتل المجاورة ≈ 0.44 عند استمرارية شهرية 0.8)، ليس خطأً برمجياً. لم أخفّف المعيار؛ أضفت ثلاث حالات للإشهاد: «معتمد كلياً» (لا أحد حالياً)، «معتمد مشروطاً على E\_core» (ممكن لـ IM-4 عند K=60 فقط وبافتراض غير قابل للتحقق)، «غير معتمد».
2. **صافي R لكل شهر تقويمي كمقياس أساسي:** مقترح مع تبعاته: العتبات تتحول إلى R/شهر (0.10R لكل صفقة = 0.5R/شهر عند 5 صفقات)، ووحدة العينة تبقى K شهراً ثابتاً (تُزال مشكلة « K الفعال = الأشهر النشطة »)، لكنه لا يصلح المعايرة نفسها.
3. **قواعد المهارة التنبؤية:** ثلاث ادعاءات (اتجاه D، توقيت T، اختيار نظام S) لكل منها null وتوزيع مرجعي، ادعاء أساسي واحد يُحدَّد عند التجميد من مجموعة مسموحة حسب نوع الاستراتيجية، p الادعاء = أكبر p لبواباته (تقاطع-اتحاد)، Holm عبر الاستراتيجيات، سجل مسارات التحليل لمنع الانتقاء اللاحق، ولا ادعاءات احتياطية بلا تسجيل مسبق. حد لا يُتجاوز: اختبار S لا يبلغ p ≤ 0.01 على 24 شهراً (دقة ≈1/24).
4. **التصنيف:** حُذف شرط «لا نظام سلبي» من Class 1 (التجانس لا ينقض أفضلية عامة على العينة الكاملة)، وأضيفت فلاتر وصفية بلا فيتو. نتيجة مهمة: بمقياس R/شهر، **الفلتر يضيف قيمة إذا وفقط إذا خسرت الصفقات المستبعدة** (متطابقة رياضية)، فربحية النظام الصاعد لا تُثبت قيمة الفلتر.
5. **الأدلة المستقبلية:** تصميم بمتسلسلات ثقة صالحة في أي وقت (شرطها حدود معلنة للخسائر)، نظام تنفيذ ظلي مع سجل لا يُعدّل، نظرات مجدولة فقط تُصدِر الحكم، إيقاف للفعالية/الرفض/الضرر، معالجة تغير التكاليف دون حذف أشهر. **لكنه لا يستطيع تأكيد حافة 0.10R لكل صفقة في أي إطار زمني بشري** (10–50 سنة)، ويستطيع حافات 0.3–0.5R خلال نحو 0.4–5.5 سنة (تقدير متفائل).
6. **التدقيق:** وجدت أخطاء فعلية في V2 وصلحتها في القسم 1 بجدول من 16 بنداً: Block Bootstrap ليس «أسوأ في كل سيناريو» (أسوأ في 11 من 13 عند K=24، وأفضل قليلاً مع الاستمرارية القوية)، وانحراف الصفقة في المولد هو 1.414 لا 1.5، ونطاقات عدة أرقام كانت خاطئة، ووحّدت رقم Block Bootstrap بتعريف واحد للمجموعات.
7. **تخصيص البيانات:** اعتمدت توصيتك: لا إعادة استخدام VALID/HOLD بين v1.2 وv2، نوافذ v1.2 محفوظة وغير مُشغّلة، v2 بسجل مستقل وأدلة تأكيد مستقبلية فقط، مع شرطين: تاريخ نهاية HOLD يُسجَّل وجدار معلوماتي بين البروتوكولين. ثمن ذلك: v2 لا يملك أدلة تأكيد تاريخية إطلاقاً.

**الخلاصة الصريحة:** ببياناتنا لا يمكن إثبات ضبط خطأ موحّد عند استمرارية قوية على 24 شهراً، ولا كشف حافات متواضعة بشكل متاح، ولا معايرة اختبارات الحافة الشرطية قيل لم تُجرَّ بعد. النتيجة المعتادة لأغلب الاستراتيجيات ستكون «غير حاسم — قوة غير كافية»، وهذا تشخيص صادق لا فشل في التصميم. القرارات الثمانية المطلوبة منك في القسم 8.2.

## 0. Status, tags and scope

This is a design and review document only. No code was written, no simulation was run, no project file was changed, DEV/VALID/HOLD were not touched, protocol v1.2 and PR #5 are unchanged. The only new computation is arithmetic and re-reading of **existing** audit CSV files (`docs/audit/t6_*.csv`, `t7_*`, `t8_*`) to check V2's numbers.

**Tags.** **\[V\]** = verified: measured in my synthetic audits (branch `statistical-audit-2026-11`) — true only inside the synthetic generators I chose. **\[T\]** = theoretical or arithmetic argument, not simulated; where it rests on literature I recall rather than checked, it says so. **\[P\]** = proposed design or experiment, nothing run.

**Rule for this version.** No criterion is loosened to make a method pass. Where the data cannot support a goal, the document says "not provable with our data" and Section 8 lists those goals in one place.

| # | Your point | Where | Outcome in one line |
| --- | --- | --- | --- |
| 1 | D2 vs Ibragimov–Müller 2.5× | §2 | the conflict is real; **no tested method meets D2**; IM-4 fails by its own premise, not by a bug |
| 2 | calendar-month net R as primary | §3 | adopted as a proposal; changes units, thresholds, power and the filter test |
| 3 | pre-registered skill rules | §4 | one primary claim chosen by strategy type; fixed-sequence for the rest |
| 4 | Class 1 and filter value | §5 | the "no negative regime" veto is removed; in-regime profit and filter value are separate claims, and with R/month the filter has value only if the outside-regime trades lose money |
| 5 | prospective evidence | §6 | confidence-sequence / e-process design with spending, looks, stopping, cost handling; **it cannot confirm 0.10R/trade in any human time frame** |
| 6 | audit of numbers | §1 | V2 contained errors (listed with corrections) |
| 7 | data allocation | §7 | adopted: no VALID/HOLD reuse between v1.2 and v2; v2 confirmation is prospective only |

## 1. Numerical audit of V2 — errata and corrected figures

Every V2 figure was re-derived from the committed CSV files or by arithmetic. **V2 contained errors**, listed here. Ratios are *actual / nominal* rejection rate at nominal level 0.00125, point estimates, 100,000 datasets per cell (`t6_size.csv`). Two fixed scenario sets are used so that ranges are comparable everywhere in this document:

- **Benign set** = N1 (iid normal), N2 (iid rr2), T1 (trade AR 0.1), M1 (month effect, iid), V1 (volatility, iid).
- **Dependence set** = S1 (streaks), T3 (trade AR 0.7), M2 (month effect AR 0.5), M4 (month effect 0.25, AR 0.8), M3 (month effect 0.5, AR 0.8).
- The other three (T2, V2, V3) are reported only in "all 13 scenarios".

### 1.1 Corrections

| # | V2 statement | Status | Corrected statement \[V unless tagged\] |
| --- | --- | --- | --- |
| 1 | Arabic summary: block bootstrap "4.7–52× at K=24"; table: "4.3–52×" | **inconsistent** | Circular block bootstrap (block 3), K=24: benign set 3.9–7.2×; dependence set 7.9–52.1×; all 13 scenarios 2.3–52.1×. K=60: benign 1.2–2.6×; dependence 3.0–34.5×; all 0.5–34.5×. One definition is now used everywhere |
| 2 | "block bootstrap was worse than the iid-month bootstrap in every scenario" | **false** | CBB is worse in 11 of 13 scenarios at K=24 and 8 of 13 at K=60. It is *better* under strong persistence: K=24 M3 52.1 vs 56.0, T3 7.9 vs 8.6; K=60 M2 7.2 vs 10.1, M3 34.5 vs 53.3, M4 13.0 vs 13.9, S1 4.7 vs 5.5, T3 3.0 vs 6.1. Honest summary: it pays 2–4× more inflation in benign cells for a partial gain in persistent ones, and stays 3–52× inflated in the dependence set |
| 3 | production bootstrap "1.4–3× under independence at K=24; 0.8–1.6× at K=60" | **range wrong** | benign set K=24: 1.0–3.0×; K=60: 0.5–1.6× (V1 0.47, N2 0.81). Dependence set: 7.9–56.0× (K=24), 5.5–53.3× (K=60) |
| 4 | t-test "0.6–1.0× independent; 6–47× persistence" | **range wrong** | benign set 0.40–0.99× (K=24), 0.41–1.03× (K=60); dependence set 3.8–38.4× (K=24), 4.3–47.3× (K=60) |
| 5 | Newey–West "0.4–4×; 6–33×" | **range wrong** | lag 1, benign 0.8–1.7×, dependence 2.7–33.2× (K=24); lag 3, benign 2.2–4.0×, dependence 4.5–32.6×. K=60 does not improve (lag 1 dependence 2.3–34.8×) |
| 6 | fixed-b "≤3.1× moderate, 9.5× severe" | consistent, restated | dependence set 1.1–9.5× (K=24), 0.9–5.0× (K=60); 95% upper bounds up to 10.1× and 5.4× |
| 7 | IM-4 blocks "worst 2.5× (K=24), 1.6× (K=60)"; "has a size theorem" | **incomplete and too strong** | point estimates are right; the 95% **upper** bounds are 2.80× and 1.85× (both cell M3). The "theorem" is conditional and its premise fails in M3 (Section 2) |
| 8 | IM power "≤ 9% at 0.5R" | **context missing** | that is at level 0.00125 only (8.6% K=24, 25.9% K=60). At level 0.05, K=24, benign N2: 14.5% at 0.1R, 32.5% at 0.2R, 54.8% at 0.3R, 90.2% at 0.5R |
| 9 | trade sd "σ ≈ 1.5R, as in the audit generator" | **wrong attribution** | the audit's rr2 generator (+2R w.p. 1/3, −1R w.p. 2/3) has σ = √2 = 1.414. Required trades for μ = 0.10R at power 0.8, one-sided: σ = 1.414: 1,237 / 2,007 / 2,988 at α = 0.05 / 0.01 / 0.00125; σ = 1.5: 1,391 / 2,258 / 3,361. V2's "1,400 / 2,300 / 3,400" was the σ = 1.5 case. σ = 1.414 and N = 120 reproduce the measured oracle MDE (0.50R, power 0.81 at 0.5R) — so the arithmetic is validated against simulation for the audit generator **\[T validated by V\]** |
| 10 | oracle MDE "≈ 0.35R at K=60" | slightly high | theory 0.32R (N=300, σ=1.414); measured power at 0.3R is 0.747 (just under 0.8) and 1.0 at 0.5R, so MDE80 ≈ 0.32R |
| 11 | "unequal trade counts add 4–5×"; "effective K = active months" | imprecise | production p with **no dependence**: Poisson 70% active (G2) 4.1×; negative-binomial dense (G6) 5.1×; 40% active, \~9.6 active months (G10) 8.9× |
| 12 | FWER "0.146 to 0.998" | correct | 0.1458 \[0.136, 0.156\] with no dependence; 0.5918 trade-AR 0.7; 0.7280 month AR 0.5; 0.9974 month AR 0.8 (independent strategies, common resampling matrix) |
| 13 | "two calendar years may hold only 3–6 regime episodes" | **unsupported number** | illustration only. The real episode count is unknown and must be estimated from DEV prices; relabelled \[T-illustration\] |
| 14 | "6 episodes → minimum permutation p = 1/20" | true only for one split | a 3-vs-3 split of 6 episodes has C(6,3) = 20 arrangements. General rule \[T\]: minimum one-sided exact p = 1 / C(E, a). A 6/6 split needs E = 12 (C = 924, p\_min = 0.0011) to reach 0.00125 |
| 15 | B2: circular shift "calibrated in every timing model tried" | **scope not stated** | that was the *event-study* statistic (supplement §5), not strategy P&L. For strategy returns it is untested \[P\] |
| 16 | D4 simulation counts (35,000 / 140,000 / 3,500 / 7,300) | arithmetic correct | but they verify **one cell**; the full envelope multiplies them by the number of cells (e.g. 13 scenarios × 2 K × methods) |

### 1.2 What did not change

The core findings of the audits are unaffected: the production monthly bootstrap is not a controlled test at the Holm-equivalent level; more resamples do not fix it; Holm is arithmetically correct but needs valid marginals; and the sample is too small for modest edges.

## 2. D2 against Ibragimov–Müller: the calibration conflict

**Finding: the conflict is real. No method I tested meets D2 as written, and I do not call any method guaranteed or adopted.**

### 2.1 The facts \[V\]

D2 (V2): per-test Type-I error at levels 0.05, 0.01, 0.00125 must have a 95% **upper** bound ≤ 1.5× nominal in **every** envelope cell. The envelope here is the 13 scenarios of the supplement audit; K = 24 and K = 60 months; 100,000 datasets per cell. IM-4 = Ibragimov–Müller test on 4 contiguous blocks (t with 3 df).

| IM-4 (4 blocks) | level 0.05 | level 0.01 | level 0.00125 |
| --- | --- | --- | --- |
| K=24: largest upper bound | 1.96× (M3) | 2.50× (M3) | 2.80× (M3) |
| K=24: cells with upper > 1.5× | 1 (M3) | 2 (M3, M4) | 3 (M2 = 1.51, M3, M4 = 1.71) |
| K=60: largest upper bound | 1.39× | 1.57× (M3) | 1.85× (M3) |
| K=60: cells with upper > 1.5× | none | 1 (M3) | 1 (M3) |

Point estimate in the worst cell: 313 rejections in 100,000 at nominal 0.00125 (expected 125) = 2.50× \[2.23, 2.80\]. Every other tested method is worse: fixed-b has upper bounds up to 4.1× (0.01) and 10.1× (0.00125) at K=24; the production bootstrap up to 56× (Section 1).

### 2.2 Why IM-4 fails — the premise, not a bug

&#91;T\] The IM result (Ibragimov & Müller 2010, as I recall it; not re-derived here) says: if the q block statistics are approximately **independent** normal variables with possibly different variances, the t-test with q−1 degrees of freedom has size ≤ α for α up to about 0.08. The guarantee is therefore *conditional on block independence and block normality*, and is asymptotic in the sense that blocks must be long enough for the CLT and for dependence to fade between them.

&#91;T arithmetic\] In cell M3 the month series is AR(1) with φ = 0.8. For two adjacent 6-month blocks of such a series the correlation between block means is **0.44** (0.14 for φ = 0.5). The premise is violated, which is exactly what the data show: 2.5× in M3, 1.3× in M2 (φ = 0.5, correlation 0.14), ≈ 1 in the benign cells. At K = 60 the blocks are 15 months long, adjacent-block correlation falls, and the worst ratio falls to 1.6×. So my V2 phrase "has a size theorem" was too strong: it has a theorem with a premise that fails in our harshest cell.

### 2.3 Is there a method that meets D2?

- **Among the methods tested: no \[V\].** At K=24 none meets it at any of the three levels; at K=60 IM-4 meets it at level 0.05 and fails in a single cell, M3, at 0.01 (upper bound 1.57×) and 0.00125 (1.85×).
- **Among untested variants: unknown \[P\].** Candidates and what I expect, as hypotheses not facts: fewer blocks (q = 3: critical value at 0.00125 is t = 20.0; q = 2: t = 254.6, i.e. almost no rejection ever); more blocks (q = 6: t = 5.6, better power but premise fails more at K=24); blocks aligned to regime episodes instead of calendar thirds (needs labels); a conservative multiplier (use level α/c with c the worst-case inflation, but the inflation ratio itself changes with the level, so it must be re-measured at the adjusted level); bounded-increment confidence sequences (Section 6).
- **A general reason to expect none with useful power \[T, literature recall — not verified here\].** Impossibility results for inference under unrestricted dependence (Dufour 1997 for confidence sets over unrestricted parameter spaces; Müller 2014 for strongly autocorrelated series) imply that a test whose size is controlled uniformly over arbitrarily persistent dependence with a short sample must have very low power. 24 monthly observations cannot distinguish a persistent regime effect from a true mean. I treat this as a prior to be tested in the calibration program, not as a proven statement about our setting.

### 2.4 What D2 can and cannot mean (no loosening)

D2 stays as the **full-certification** criterion. I add three status words, not new thresholds:

| Status | Definition | Current status \[V\] |
| --- | --- | --- |
| **Fully certified** | D2 holds on the whole declared envelope (including the persistent-regime cells) | **No tested method, at K=24 or K=60** |
| **Conditionally certified on E\_core** | D2 holds on a declared sub-envelope E\_core; the cells excluded from E\_core are listed as **unverifiable assumptions** ("month-level persistence φ ≤ 0.5" is not something VALID or HOLD can confirm without being consumed) | IM-4 **on E\_core = all cells except M3 and M4 (the two φ = 0.8 month-persistence cells). K=60: passes at all three levels (largest upper bounds, all in M2: 1.08× at 0.05, 1.16× at 0.01, 1.30× at 0.00125). K=24: passes at 0.05 (1.23×) and 0.01 (1.31×) and fails narrowly at 0.00125 (M2 upper bound **1.51×) |
| **Not certified** | otherwise | everything else, including every method at K=24 and every level ≤ 0.01 |

A conditionally certified method may be reported with its E\_core written next to every p-value. It may never be called "calibrated" without it.

### 2.5 The price of the certified method is power

IM-4, benign cell N2 (iid, rr2) \[V\]: power at 0.5R/trade at level 0.00125 is 8.6% (K=24) and 25.9% (K=60); at level 0.05 it is 90.2% and 99.8%. At 0.2R/trade and level 0.05: 32.5% (K=24), 58.9% (K=60). So the certified test is usable **only at levels around 0.05 and only for edges ≥ 0.3–0.5R/trade at K=24** — a statement about the test, not about the strategy.

Consequence for family size \[T\]: a per-test level of 0.00125 (Holm over 82 hypotheses) is incompatible with any certified test available at our sample sizes. v2's confirmatory family must therefore be small by *pre-registration* (one primary claim per strategy, a handful of strategies), which is a design consequence of the evidence budget, not a threshold chosen to let hypotheses pass.

### 2.6 What must be run before anything is called calibrated \[P\]

IM with q ∈ {3, 4, 5, 6, 8}, calendar vs episode-aligned blocks, the worst-case-multiplier idea at its adjusted level, bounded-increment confidence sequences, the whole envelope plus any cells you add, K ∈ {24, 36, 60, 120}. Nothing is run until you approve the calibration program.

## 3. Primary economic measure: net R per calendar month \[P\]

**Proposal.** Primary estimand: θ = E\[Yₘ\], where Yₘ is the net R (after the declared cost model) booked in calendar month m, **empty months counted as 0**, evaluated over the K calendar months of the window. Secondary: mean net R per trade. Every number below that depends on this choice is flagged.

### 3.1 Definitions that must be frozen with the strategy

- Month grid in a fixed time zone (UTC), not server time (GMT+2/+3 changes the grid twice a year).
- Trade-to-month rule: **exit time** of the realised trade; trades still open at the window end are marked to market at the last bar and flagged (or excluded by a rule stated in advance — never by looking at their sign).
- R unit fixed at entry from the stop distance; costs included; concurrent positions add.
- A month with no closed trade is Yₘ = 0; the number of such months is reported next to every result.

### 3.2 Consequences

| Aspect | Consequence | Tag |
| --- | --- | --- |
| Units and thresholds | R/month = trades per month × R/trade. v1.2's 0.10R per trade is **not** the same threshold: at 2 / 5 / 10 trades per month it equals 0.2 / 0.5 / 1.0 R/month. The minimum economic effect must be declared **in R/month** at freeze; a high-frequency weak edge and a low-frequency strong edge can tie. I do not propose a number: it is your decision | T |
| Sampling unit | K is the number of calendar months in the window (24 for VALID-sized data) whatever the activity. This removes the artefact in which the effective K equals the number of active months (production p with no dependence: 8.9× at \~9.6 active months, 5.1× with negative-binomial counts) | V (problem), T (removal) |
| Calendar-axis methods behave better | in the gap study at K=24, level 0.00125: production p 1.5× (dense, equal counts, no dependence) up to 52.3× across the ten gap scenarios, calendar-axis fixed-b up to 23.1×, calendar-axis IM-4 at most 2.3× (G7). The calendar axis helps; it does **not** make anything certified (Section 2) | V |
| What it does not fix | dependence between months and persistent regimes: every method with p-values still has the inflation of Section 1 | V |
| Power, equal activity | identical to per trade: signal-to-noise = √N · μ/σ either way | T |
| Power, varying activity | the monthly total carries extra variance ≈ μ²·Var(nₘ) from fluctuating counts — negligible when μ/σ ≈ 0.1 — and months with many trades dominate the variance (volatile months are both noisier and busier). Sparse strategies give monthly totals that are mostly zeros with a few large values: normal approximations are poor and t-based intervals are the least trustworthy there | T |
| Minimum detectable effect (oracle sd, iid months, K=24, 80% power) | see table below; MDE per trade falls like 1/√n with activity | T |
| Filter test | the paired contrast filtered − unfiltered equals minus the total R booked on trades **outside** the regime; see Section 5 | T |
| Skill controls | controls must reproduce each month's trade count to give an excess per month; this constrains feasible controls in busy months and is a calibration item | P |
| Month boundaries | exit-time assignment leaves lag-1 dependence between adjacent months (a D1 trade can span a month end); a half-month grid shift is a descriptive sensitivity check, not a test | T / P |
| Portfolio view | monthly R is additive across strategies, so cross-strategy dependence becomes the covariance of monthly vectors, which a joint (Max-T) resample can use | T |

**MDE at K=24, σ = 1.414R/trade, oracle variance, DE = 1 \[T\]:**

| trades per month | MDE (R/month) at α = 0.05 | MDE (R/trade) at α = 0.05 | MDE (R/month) at α = 0.00125 | MDE (R/trade) at α = 0.00125 |
| --- | --- | --- | --- | --- |
| 2 | 1.01 | 0.51 | 1.58 | 0.79 |
| 5 | 1.60 | 0.32 | 2.50 | 0.50 |
| 10 | 2.27 | 0.23 | 3.52 | 0.35 |

The n=5 row at 0.00125 matches the simulated oracle MDE (≈ 0.50R/trade) \[T validated by V\]. Dependence multiplies the variance by the design effect and **raises every entry**; the real design effect is unknown.

### 3.3 The secondary measure

Mean net R per trade is reported with its interval, for cost-sensitivity, for comparison with v1.2's expectancy thresholds, and where the skill controls are per trade. It has **no gate**: it can neither rescue a failed primary result nor veto a passed one. The stressed-cost condition applies to the primary measure (R/month under the stressed cost scenario).

### 3.4 Honest limit

Choosing R/month fixes *what* is estimated; it does not fix *how well*. With 24 months the interval for θ is wide whatever the unit, and the statement of Section 2 stands: it cannot be certified.

## 4. Predictive skill: pre-registered rules for direction, timing and regime selection \[P\]

Goal: the test that is run, its null, its reference distribution and its place in the multiplicity scheme are fixed **before** any result for that strategy exists, and cannot be swapped for whichever one "worked".

### 4.1 Three claims, three nulls

| Claim | Question | Statistic (monthly unit, §3) | Null | Reference distribution | Applies to |
| --- | --- | --- | --- | --- | --- |
| **D** direction skill | does the signalled side beat the opposite side at the same entries? | mean over entries of the net R of the actual side minus the net R of the counterfactual opposite side, with identical stop, RR, max hold and costs | side is independent of the outcome difference | sign-flip of entries performed by whole calendar months, because entry-level flips ignore serial dependence | strategies that take both sides |
| **T** timing skill | given side and geometry, do entry times carry information? | excess net R per month over circularly time-shifted copies of the signal set (same side, geometry, count per month) | timing is independent of the price series | circular shifts on the calendar axis | one-sided strategies with entry content, and the in-regime part of conditional strategies |
| **S** regime-selection skill | does the regime label pick better periods than a random label with the same duty cycle and persistence? | filtered minus unfiltered net R per month, paired | label is independent of strategy returns | circular shifts of the label series, which preserve duty cycle, persistence and episode lengths | strategies whose only content is a regime filter, with no entry content |

Why a drift cannot masquerade as skill \[T\]: D compares two trades at the same bar, so a drift moves both sides in opposite directions and cancels in the difference when the side is truly random; T and S shift the signal or the label against a fixed price path, so drift and volatility structure stay in the reference. An always-long strategy has no D claim (no variation in side) and, with no entry content, only S.

### 4.2 Binding rules

1. **One primary skill claim per strategy**, named at freeze from the allowed set of its type (two-sided: D, T, S; one-sided with entry content: T, S; regime-only exposure: S). The choice is hashed into the registry entry and cannot be changed afterwards.
2. **A claim's p-value is the maximum of the p-values of all gates it requires** (intersection–union). Example: Class 3 with timing needs p = max(p\_economic, p\_T). No α is split between gates.
3. **No reselection.** The pipeline computes D, T and S for every strategy where they are defined and writes all of them to a *forking ledger* (statistic, code hash, seed, time). Only the declared one can enter a classification. The others are labelled "exploratory — not evidence" in the report and cannot be cited as support.
4. **No fall-back claims.** If the declared Class 3 fails, the strategy is not awarded Class 1 or 2 as a confirmed label on the same data. A fall-back is a second hypothesis and must be **registered beforehand** as its own family member; its price is explicit (a larger family).
5. **Reference distribution, resample count B, seed and α are fixed at freeze.** p = (1 + #{ref ≥ obs}) / (1 + B), one-sided. Resolution rule: the number of **distinct** reference values must be at least 10/α\_claim; otherwise the claim is evaluated only at the coarser level its resolution allows and the verdict says so.
6. **One-sided only.** A two-sided p is never used to rescue a one-sided claim.
7. **Missing p counts as 1** (as v1.2 already does for the not-evaluable control).
8. **A claim can be called "confirmed" only if its test has passed calibration (D2-type) on the skill scenarios** (drift without skill, persistent regimes, misclassification). Otherwise the label is "uncertified".
9. **Code or definition change after freeze = new strategy hash** and counts as an exposure of the validation window (Section 6).

### 4.3 Multiplicity

- **Within a strategy:** none beyond rule 2 — one declared claim, one p (the maximum over its gates).
- **Across strategies:** the confirmatory family is every declared claim of every registered strategy, **including regime variants and any registered fall-back claims**; Holm on the claim p-values. Holm needs valid marginal p-values: that is what the calibration of rule 8 is for, and Holm alone repairs nothing.
- **Instruments and timeframes:** XAUUSD/EURUSD and D1/H4 versions of one rule are separate family members (correct for multiplicity) but are *not* counted as independent confirmations (they share the USD factor and most of the information).
- **Triage in DEV:** discovery-stage false-discovery-rate control is allowed because no confirmatory claim is made there.

### 4.4 Limits that cannot be removed \[T\]

- **Resolution of S.** Circular shifts of a label series on a 24-month window give at most 23 distinct monthly shifts, so the smallest attainable p is 1/24 ≈ 0.042 (bar-level shifts give more values but they are highly correlated: the effective number is of the order of the number of regime episodes). **S cannot reach levels of 0.01 or below on a VALID-sized window**, whatever its power.
- **Power of T and D** at the monthly unit is bounded by the MDE table of Section 3.
- **D needs the counterfactual opposite-side trade from the engine.** If the engine cannot produce it with identical stop/RR/costs, D is not available.
- **None of the three has been calibrated.** \[P\] The calibration program of V2 §D (scenarios 2, 4, 5, 9) is the test.

## 5. Classification: Class 1 revised; in-regime profit versus filter value \[P / T\]

### 5.1 Class 1 without the "no significantly negative regime" veto

You are right. In V2 the veto turned heterogeneity into rejection. Reasons it should go \[T\]:

- A full-sample general edge is a statement about **the regime mix that occurred in the window**. Differences between regimes do not contradict it; they describe where it came from.
- The veto has almost no power to fire honestly (a regime-level test has few episodes) and when it does fire it is as likely multiplicity noise as signal; and the more regimes are reported, the more chances to veto. That punishes transparency.

**Class 1 (general economic edge on the sample regime mix):** confirmatory claim on the **unfiltered** strategy over the whole evaluation window — the lower bound of the interval for θ (R/month, §3) is at least the declared minimum after stressed costs, from an inference method with at least conditional certification (§2.4). Nothing about individual regimes enters the gate.

Descriptive companions, none of which can veto or promote:

1. regime-wise estimates with intervals;
2. **mixture stress**: θ recomputed with equal regime weights and with the worst declared regime share — a measure of how much the edge depends on the regime mix continuing;
3. an **"adverse regime documented" flag** when a regime's interval lies entirely below zero with at least a declared share of trades. The class does not change; the flag generates a *candidate* for a new filtered strategy, which must be registered as a new hypothesis and confirmed on **new** data.

The Class 1 label always carries the words "on the sample regime mix".

### 5.2 Profit inside a regime is not value added by the filter

Let π\_in and π\_out be the expected net R per month booked by trades taken inside and outside the declared regime. The unfiltered strategy earns π\_in + π\_out, the filtered one π\_in. Then, in the primary unit of §3:

> **Filter value in R/month = π\_filtered − π\_unfiltered = −π\_out.** \[T, exact identity\]

Hence **the filter adds total R/month if and only if the trades it removes lose money after costs.** A regime in which the strategy earns well says nothing about this; a regime in which it earns *less* is not a reason to filter it out if it still earns something.

Worked example \[T, illustrative numbers\]: your per-trade expectancies bullish +0.25R, bearish −0.05R, sideways +0.01R, with 2.0 / 1.5 / 1.5 trades per month. Bullish adds +0.50, bearish −0.075, sideways +0.015 R/month. Filtered (bullish only) = +0.500; unfiltered = +0.440; filter value = +0.060 R/month. Standard error of that contrast over 24 months (3 trades/month outside, σ = 1.414, iid) ≈ 0.50 R/month, i.e. the filter's value is 0.12 standard errors. The in-regime profit itself (+0.50 R/month, SE ≈ 0.41) is only about 1.2 standard errors. **Both are far from detectable in 24 months**, and the second claim (filter value) is the weaker of the two.

When can a filter add value although −π\_out ≤ 0? Only on another metric: R per trade, drawdown, time in the market, capital efficiency, correlation with other strategies. Then the **metric must be named at freeze** (for instance "R/month per unit of maximum R-drawdown"); choosing it after seeing which one favours the filter is exactly the forbidden reselection.

Two different claims, two different nulls:

| Claim | Meaning | Null | Section |
| --- | --- | --- | --- |
| **P** in-regime profit | π\_in ≥ declared floor after stressed costs | π\_in below the floor | Class 2 gate |
| **F** filter value | −π\_out > 0 (total R/month), or the declared risk-adjusted metric improves | π\_out ≥ 0 (or no improvement) | attribute, §5.3 |
| **S** regime-selection skill | the label beats a random label with the same duty cycle and persistence | label independent of returns (§4.1) | attribute, §5.3 |

F is about the realised economic effect of removing trades; S asks whether the label is informative at all. F can hold while S fails (the outside losses may be luck), and S can hold while F fails (informative label, but the excluded trades still earn something).

### 5.3 Revised classification (replaces V2 §E2)

| Class | Claim registered at freeze | Gates (claim p = max of the gate p-values) | Not implied |
| --- | --- | --- | --- |
| 1 General economic edge on the sample regime mix | unfiltered strategy | economic gate | any statement about a single regime; skill |
| 2 Conditional economic edge | filtered strategy inside a frozen regime | P: economic gate on in-regime trades, stressed costs; feasibility passed | filter value; skill |
| 3 Predictive skill | unfiltered strategy | Class 1 gate and the declared primary skill claim (D or T) | any regime statement |
| 4 Conditional predictive skill | filtered strategy | Class 2 gate and T (or D) **inside the regime** against the regime-matched benchmark | filter value |
| Attribute F / S | declared separately | F or S as in §5.2, only if registered as its own claim | any class by itself |
| 5a Rejected | any | interval excludes the declared minimum effect |  |
| 5b Inconclusive: insufficient power | any | design MDE exceeds the claimed effect; interval contains 0 and the minimum |  |
| 5c Provisional: uncertified inference | any | the only available test has no (conditional) certification at this sample (§2.4) | **cannot be called Confirmed** |

A "Confirmed" label requires at least conditional certification of the inference method; otherwise the best possible verdict is 5c. A strategy may register more than one claim (for instance Class 1 and Class 4); each is a separate family member (§4.3). No automatic promotion between classes, and no fall-back class on the same data.

## 6. Prospective evidence protocol after freeze \[P / T\]

Everything in this section is design. The literature statements are recalled, not re-checked here, and **no width, power or cost figure below has been simulated**.

### 6.1 Set-up

- **Registry.** A separate v2 registry (Section 7), hash-chained. A **freeze event** records the strategy hash (signal, regime definition and thresholds, estimand, cost model, claim and class, minimum effect, caps, looks, T\_max, seeds). The prospective window starts at the first full calendar month **after** the freeze event.
- **Data generation.** Orders are produced by the frozen code on live prices in shadow (paper) mode or at minimal size, written to an append-only log with timestamps; real quoted spread, commission and slippage are recorded per trade. No retrospective edit; a code change is a new strategy hash.
- **Unit.** Yₛ = net R in calendar month s, marked to market at month end (realised plus change in open P&L, in R), empty months 0. Marking to market removes the look-time bias of counting only trades that have already closed.
- **Cohorts.** Strategies frozen on the same date form a cohort. A global error budget (for example α\_total = 0.10) is split across cohorts by a pre-declared schedule (for example cohort c receives 0.10·2⁻ᶜ), so future cohorts can be tested without exceeding the total.

### 6.2 Inference: two layers

**Layer A — primary: anytime-valid confidence sequence \[T, literature recall\].** Target: the running average of conditional expectations θ̄ₜ = (1/t)∑ E\[Yₛ | past\]. The increments Yₛ − E\[Yₛ | past\] form a martingale difference sequence; with **bounded** Yₛ (declared caps: maximum trades per month and a worst-case loss per trade including gaps, fixed before the window) betting / empirical-Bernstein confidence sequences (Howard, Ramdas, McAuliffe & Sekhon 2021; Waudby-Smith & Ramdas, bounded-mean methods) are valid **at every time simultaneously**.

| What it protects | What it does not protect |
| --- | --- |
| optional stopping: any number of looks, any stopping rule | unbounded jumps: if a loss exceeds the declared cap the guarantee is void — the cap is an assumption |
| arbitrary persistence in the conditional mean (regimes, serial dependence of expected returns) | a non-stationary edge is not estimated as one number: the target is the average over the window, so a decaying edge is averaged, not detected |
| no asymptotics, no block length, no variance estimator from 24 points | conservatism: widths are larger than a fixed-sample interval at the same horizon; by how much is **unmeasured** (calibration item) |
| arbitrary dependence between strategies (use the union bound over a cohort at level α\_cohort/m, or e-value closed testing) | — |

**Layer B — secondary: spending over fixed looks \[T/P\].** Looks at 12, 24, 36, 48, 60 months with pre-declared weights wₖ summing to 1 and level αₖ = α·wₖ each (union bound over looks: valid under any dependence between looks). Each look uses the interval method that has passed the D2-type calibration **at that K** (IM-type blocks, Section 2). Until it has passed, Layer B is reported but is "uncertified".

**Decision rule.** The verdict follows Layer A. Layer B is a cross-check; if they disagree both are reported and the verdict stays at the weaker one.

### 6.3 Looks and stopping rules (all pre-registered)

1. **Scheduled looks** at calendar month ends; the first no earlier than 12 months **and** at least a declared number of trades; for conditional claims also at least a declared number of regime episodes observed in the window (measured on prices only).
2. **Efficacy stop:** lower bound of the Layer A sequence ≥ the declared minimum effect (R/month, after realised costs) → verdict Confirmed for the registered class. Later data cannot overturn it, and monitoring continues for operations only.
3. **Rejection stop:** upper bound < the declared minimum effect → 5a Rejected. **Harm stop:** upper bound < 0, or a declared drawdown limit → stop trading, 5a.
4. **T\_max** declared (for example 60 months): neither bound crossed → 5b Inconclusive.
5. **Unscheduled looks** are permitted (anytime validity) but **only scheduled looks can trigger a verdict**, removing discretion.
6. **Modification** of any frozen element = new hash, new clock; months already observed cannot be reused to confirm the new hash.
7. **Skill claims** are not anytime-valid when built from shifted reference distributions. Two routes: (a) fixed looks with Bonferroni-weighted levels (as Layer B), or (b) a randomisation-martingale form: each month, controls are **drawn fresh** from the declared null law (random matched entries for T, random sign for D), and Zₛ = Yₛ − control mean (or εₛΔₛ) is a bounded martingale difference under the null, so Layer A applies to Z. For S the label null needs a law for label persistence — an assumption — so S uses route (a) only. All of this is unverified \[P\].

### 6.4 Costs and temporal dependence

- **Two series are recorded:** Yₛ under **realised** costs and Yₛ under the frozen cost model. The economic gate uses realised costs (what was tradable); skill claims use gross R or controls that share the same costs.
- **Cost breach:** if realised cost per trade exceeds the frozen pessimistic scenario by a declared factor for a declared number of consecutive months, a breach flag is set. Months are **never excluded** (exclusion would be selection). While the flag is on the best verdict is 5c; a new cost assumption means a new strategy hash and a new clock.
- **Cost in R moves with volatility** (cost/stop). That is part of the conditional mean and is allowed for by Layer A; it is a reason to report both series.
- **Dependence in time:** the conditional-mean dependence is covered by Layer A; month-end overlaps by the marking rule; dependence in conditional *variance* is covered because widths use the realised variance process (empirical Bernstein) or the declared range.

### 6.5 How long would it take? \[T — fixed-sample, oracle variance, DE = 1; the real answer is longer\]

Months needed for 80% power, σ = 1.414R per trade, one-sided, per-trade edge μ, at 5 and 10 trades per month. Confidence sequences need more than these fixed-sample figures; dependence needs more still.

| edge μ (R/trade) | trades at α = 0.05 / 0.01 / 0.00125 | months at 5 trades/month | months at 10 trades/month |
| --- | --- | --- | --- |
| 0.10 | 1,237 / 2,007 / 2,988 | 247 / 401 / 598 (20 / 33 / 50 years) | 124 / 201 / 299 (10 / 17 / 25 years) |
| 0.20 | 309 / 502 / 747 | 62 / 100 / 149 (5 / 8 / 12 years) | 31 / 50 / 75 (2.6 / 4 / 6 years) |
| 0.30 | 137 / 223 / 332 | 27 / 45 / 66 (2.3 / 3.7 / 5.5 years) | 14 / 22 / 33 (1.1 / 1.9 / 2.8 years) |
| 0.50 | 49 / 80 / 120 | 10 / 16 / 24 (0.8 / 1.3 / 2 years) | 5 / 8 / 12 (0.4 / 0.7 / 1 year) |

**Plain reading.** An edge of 0.10R per trade cannot be confirmed on D1/H4 XAUUSD or EURUSD within any human time frame at any of these levels, with or without a prospective tier. Edges of 0.3–0.5R per trade can be confirmed in roughly 0.4 to 5.5 years at 5–10 trades per month, depending on the level (fixed-sample figures; real ones are longer). A smaller confirmatory family (larger α per test) shortens the time but is a consequence of registering fewer hypotheses, not a way to make a 0.10R edge testable.

### 6.6 Status of this section

- **\[V\]:** none. No sequential procedure has been run.
- **\[T\]:** the martingale structure of Layer A, its validity under bounded increments, the arithmetic of 6.5 (checked against the simulated oracle MDE for N=120, Section 1 item 9).
- **\[P\]:** all caps, weights, looks, T\_max, cohort budget, the randomisation-martingale skill route and the cost-breach rule. They are to be fixed by you and the reviewer and then calibrated on synthetic data with scenarios added in V2 §D: edge decay (scenario 11), cost drift (12), repeated cycles (13), regime persistence (5), plus a new scenario with **unscheduled peeking** to confirm that only scheduled looks decide.

## 7. Data allocation between v1.2 and v2 \[P — your recommendation adopted\]

**Adopted as the working rule: VALID and HOLD are not reused between v1.2 and v2.** The v1.2 windows stay reserved for the 15 registered v1.2 hypotheses and are **not run** until a separate decision on the validity of the inference gate. v2 has its own registry and its confirmation evidence is **new, prospective data**.

### 7.1 What each protocol may use

| Data | v1.2 | v2 |
| --- | --- | --- |
| DEV 2018–2022 | exploration only, as locked (no confirmatory claim) | exploration and triage only, no confirmatory claim; every variant tried is counted in the v2 registry |
| VALID 2023–2024 | reserved for the 15 registered hypotheses; **not run** pending the gate decision | **never used**, not even for feasibility counts of regime episodes |
| HOLD 2025 onward | reserved; sealed | **never used** |
| Data after the v2 freeze event | not available to v1.2 | the only confirmatory evidence |

### 7.2 Conditions that make the separation real

1. **Boundary dates.** v1.2's HOLD must end at a fixed, recorded date (the last sealed export, 2026-10-30, or whatever the registry records). Any later ingest refresh must not append to HOLD. The v2 prospective window starts at the first full calendar month after each v2 freeze event, so the two never overlap. This needs a recorded decision from you; today the HOLD definition is "2025-01-01 onward".
2. **Information firewall.** Neither protocol's design or hypotheses may be informed by results the other has produced on protected windows. Today that holds trivially (0 trials, 0 HOLD accesses). If v1.2's VALID is ever run, its outcomes must not feed v2's design.
3. **DEV is shared, but only for discovery.** A v2 hypothesis discovered on DEV cannot be confirmed on VALID/HOLD; its confirmation is prospective. DEV usage by v2 is counted in the v2 registry so the search size is known.
4. **Separate registries, separate fingerprints.** A v2 strategy hash never appears in the v1.2 registry and vice versa.
5. **Feasibility without protected data.** Regime-episode rates, activity rates and σ are estimated on DEV (or synthetic) only.
6. **Decision on the v1.2 windows.** Three states, to be decided separately: (a) stay sealed until the inference-gate decision, (b) run later under an amended gate, (c) retire as "exposed to design knowledge". Not decided here.

### 7.3 Consequences stated plainly \[T\]

- v2 gets **no** historical confirmatory data. Its first confirmed claim cannot appear before the minimum look horizon of Section 6 (12 months at the earliest, and in practice several years for edges below 0.5R per trade).
- The 2023–2026 market history becomes unusable for v2 confirmation, by design. It can still serve v1.2 later.
- If you prefer speed over cleanliness, the alternative is to let v2 own VALID/HOLD and retire v1.2's claim on them; that is the opposite choice and would need its own review. It is not what you recommended and not what this document assumes.

## 8. Feasibility ledger and decisions needed

### 8.1 What can and cannot be established with our data

| Goal | Status | Basis |
| --- | --- | --- |
| Confirmatory test with D2-type size control **uniformly over persistent regimes** at K=24 | **Not provable with our data; no tested method achieves it** | \[V\] IM-4 upper bound 2.80× (M3), all others worse; \[T, literature recall\] impossibility results |
| The same at K=60 on a declared E\_core (month persistence φ ≤ 0.5) | **Conditionally achievable for IM-4**; E\_core is an unverifiable assumption | \[V\] largest upper bounds 1.08× / 1.16× / 1.30× at levels 0.05 / 0.01 / 0.00125 |
| Detecting 0.10R per trade at any confirmatory level, from any source | **Not achievable in a human time frame** | \[T\] 1,237–2,988 trades (σ = 1.414) = 10–50 years at 5–10 trades per month |
| Detecting 0.5R per trade in VALID-sized data at α = 0.00125 | possible only with a known variance (oracle power 0.81); IM-4 power 8.6% | \[V\] |
| Detecting 0.3–0.5R per trade prospectively | feasible in roughly 0.4–5.5 years (fixed-sample, optimistic) | \[T\] |
| Regime-selection skill (S) at p ≤ 0.01 on 24 months | **Not achievable**: resolution floor about 1/24 | \[T\] |
| Filter value (F) of a modest effect | not detectable at 24 months (worked example: 0.12 standard errors) | \[T\] |
| Calibration of conditional-edge tests, interaction tests, misclassification, post-selection behaviour | **Unknown**: never simulated | \[P\] |
| Width of confidence sequences relative to fixed-sample intervals | **Unknown** | \[P\] |
| The real dependence structure of strategy returns | **Not measurable** without consuming protected data; every guarantee is relative to the declared envelope | \[T\] |

No criterion was relaxed to produce this table. Where it says "not achievable", the honest consequence is a smaller claim ("inconclusive"), not a looser target.

### 8.2 Decisions needed from you (none is made here)

1. **Envelope.** Which scenarios form the full envelope, and whether a core envelope E\_core may be declared (with its exclusions written as assumptions) for conditional certification (§2.4).
2. **Minimum economic effect** in R/month (§3.2). The document gives conversions, not a number.
3. **Primary economic unit:** R/month with R/trade secondary (§3), or the reverse.
4. **Confirmatory family size principle:** one primary claim per strategy, a small registered family, fall-back claims registered in advance (§4.2–4.3).
5. **Skill claims allowed:** D, T, S with the resolution limits of §4.4; whether S and F are admitted at all on 24-month windows.
6. **Prospective tier:** whether to build shadow execution with an append-only log, α\_total and the cohort schedule, looks, T\_max, caps (§6).
7. **Data allocation:** the recorded HOLD end date, the status of the v1.2 windows (sealed / later / retired) and the information firewall (§7).
8. **Calibration program:** approval to run it on synthetic data, with targets D2 unchanged, before any v2 rule is called adopted.

### 8.3 Carried over from V2 §G (unchanged)

Synthetic calibration shows error rates under assumed generators, not whether any strategy has an edge. Execution reality (demo data, modelled costs, 7 USD/lot assumption), instrument and timeframe dependence, decay of edges, and the researcher's prior knowledge of what has worked in gold are not removed by any test. Everything tagged \[T\] or \[P\] here is unmeasured.
