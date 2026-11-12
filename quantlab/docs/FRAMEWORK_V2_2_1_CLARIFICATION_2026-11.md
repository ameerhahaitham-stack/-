# QuantLab Framework V2.2.1 — Clarification Only

Nov 13, 2026 · @Ameer

## أ. الملخص التنفيذي (بالعربية)

هذه وثيقة توضيح وتصحيح فقط. لا تغيّر أي استنتاج في V2.2، ولا تتخذ أي قرار نيابة عنك، ولا تتضمن كوداً أو محاكاة أو وصولاً إلى DEV أو VALID أو HOLD.

1. **تعريف الملاحظة الشهرية X\_t.** كان هناك تعارض بين E.1 (المراكز المفتوحة تُقيّم عند نهاية الشهر) وA1 (ملاحظات محقّقة بالكامل). الحل: التمييز بين إغلاق الملاحظة المحاسبي (ثبات قيمة الشهر) وإغلاق الصفقة. التعريف الواحد المقترح هو X^M: التغير في قيمة الحساب بالتصفية خلال الشهر، وهو يتراكم بلا عد مزدوج ومجموعه يساوي صافي R المحقّق لكل صفقة. هذا اقتراح لك \[P\]. المشكلات المتبقية: قاعدة التقييم (mark) ومعاملة تكلفة الإغلاق (R3 وR4 في القسم 5).
2. **قاعدة التجميد أثناء جمع الدليل.** أي تعديل على الكود أو المعاملات أو الفلاتر أو إدارة المخاطر أو مصدر البيانات أو نموذج التكلفة يُصنّف ضمن فئات (0/1/2/3/3a/B). التكيّف المعلن مسبقاً لا يُبطل متسلسلة الثقة إذا كان دالة محددة من الماضي فقط؛ التغيير المؤثر يعني نسخة جديدة وادعاء جديداً، ولا يُجمع دليل نسختين مختلفتين، والمراكز تبقى لنسخة الدخول. اقتراح \[P\] لك القرار فيه.
3. **احتياطي Alpha.** لا تناقض أساسي: H توصي بنحو 20% احتياطاً، وF.6 يقسم 0.10 كاملة (بلا احتياطي). الوثيقة تعرض المحاسبتين وكلفة الاحتياطي لعائلات من 1 و٣ و٥ استراتيجيات. مثال: عند 0.10R لكل صفقة، الانتقال من 3 إلى 10 استراتيجيات يزيد المطلوب +40% بلا احتياطي و+37% مع احتياطي 20%. التوصية لم تتغير؛ القرار في حجم العائلة والاحتياطي لك.
4. **صياغة حدود إثبات T وS.** تمييز أربعة أنواع: (أ) استحالة رياضية (عدم التعرّف)، (ب) دقة إحصائية غير كافية، (ج) حلقات مستقلة غير كافية، (د) افتراضات غير صالحة. جمل V2.2 المطلقة أعيدت صياغتها بشروط العمل (نحو 60 شهراً، أداة واحدة، أنظمة بطيئة). النتيجة للمشروع الحالي لم تتغير، وتم سحب تعميمها على كل تصميم وسوق.
5. **فحص الاتساق B–I.** فُحص بالبحث المستهدف والقراءة السياقية، وليس بالإثبات سطراً بسطر. حُلّت التناقضات المذكورة أعلاه، وتبقى سبع نقاط (R1 إلى R7) في القسم 5.2، أهمها: حدود الخسارة بما يتناسب مع X^M مع مراكز متداخلة، وقاعدة التقييم وتكلفة الإغلاق، وأن أرقام F تفترض 60 شهراً بينما نافذة VALID هي 24 شهراً.
6. **ما لم يتغير وما يبقى مفتوحاً.** القرارات الستة مفتوحة ولك: الحد الأدنى للأثر الاقتصادي، نهاية HOLD، حجم عائلة التأكيد، مظلة المعايرة النهائية، اعتماد أي اختبار إحصائي، بناء التنفيذ الظلي. لا اختبار D أو T أو S معتمداً. PR #4 و#5 مفتوحان وغير مدمجين، وv1.2 لم يُمس.

## B. Change log: every modification and its reason

Each row is a clarification of a passage in V2.2. V2.2 itself is not edited; the rows below supersede the listed passages until you decide to consolidate. "Moves a conclusion" is **no** in every row.

| # | V2.2 location | Change | Reason | Moves a conclusion? |
| --- | --- | --- | --- | --- |
| 1 | E.1, first sentence | X\_t defined as the change in liquidation-value equity over the calendar month (X^M), accrual-assigned, empty month 0; open positions are marked at the bar close time of the month end | E.1 (open positions marked) and A1 (fully realised) described different observations. One definition now | No |
| 2 | E.2, A1 | Rewritten as "accounting-closed observations": the month is closed when its X\_t is fixed; positions may remain open across months | Accounting closure of the month was confused with the closure of a trade | No |
| 3 | E.9, G.1 row 1, G.3 item 3, C.5 | "closed" or "closed (fully realised)" replaced by "accounting-closed" | Same reason | No |
| 4 | D.2 row 11; B.1.4 and B.1.5 | "exit-time monthly" replaced by "accrual-assigned, month-indexed"; the failing trade-indexed CS defined as "entry-order-indexed CS (NC)" | With X^M the observation is not assigned at exit | No |
| 5 | C.3, CS row | "A1 to A5" replaced by "A1 to A6"; scenario set restated as "1, 6, 7, 8, 11, 12, 13, 14" | E contains six assumptions; the scenario set must cover the CS conditions | No |
| 6 | New (referenced from E.5 and E.7) | Strategy freeze rule during evidence collection: change classes 0, 1, 2, 3, 3a, B; claim tuple; positions belong to the version at entry; restart selection forbidden | V2.2 did not say what happens to a running CS when the strategy is edited; without it evidence can be pooled across different strategies | No (a proposal \[P\]; adoption is yours) |
| 7 | H row 3, F.6, E.7 | Both alpha ledgers shown: no reserve (0.10 split among m strategies) and 20% reserve (0.08 split among m, 0.02 held); cost of the reserve for families of 1, 3 and 5 strategies | V2.2 recommended a reserve in H and priced the family without it in F.6 | No (recommendation unchanged) |
| 8 | F.6, row m = 5, 0.10R, years | 28.0 to 27.9 | Rounding | No |
| 9 | A item 3, B.2.3, B.3.4, B.3.6, G.1 rows 4 and 5, I.1 first bullet | Absolute statements about T and S restated with the working conditions and the kind of limit (a to d) | They were read as a verdict on every design and market | No for the current project; the extension beyond it is removed |

What V2.2.1 adds that is new content, not a correction: the four-way taxonomy of limits (section 4.1), the freeze rule (section 2) and the observation definition X^M (section 1). Each is marked \[P\] or \[T\] in its own section and none is adopted.

## 1. One definition of the monthly observation X\_t

**The conflict between E.1 and A1 was real: E.1 combined exit-time assignment with month-end marks, while A1 demanded "fully realised" observations. The resolution is that A1 is a requirement on the closure of the accounting observation, not on the closure of the trade. The single definition adopted from here is the monthly change in liquidation value, X^M.** All statements are \[T\] unless tagged \[P\]. No data and no simulation are involved.

### 1.1 Two different closures

| Closure | Meaning | Needed by the confidence sequence? |
| --- | --- | --- |
| **Trade closure** | The position has exited and its outcome R\_i is final | No |
| **Observation closure (accounting)** | X\_t is fully determined by information available at the month-end instant and is never revised afterwards. Open positions may exist and enter through their marks | **Yes** (this is what A1 must say) |

### 1.2 The definition

Let V\_i(t) be the value of position i at the month-end instant of month t, in R units of its entry risk: zero before entry, the final net R\_i from exit onward, and between entry and exit the mark at the liquidation-side price net of costs already paid.

```latex
X_t^{M} = \sum_i \big[\,V_i(t) - V_i(t-1)\,\big], \qquad X_t^{R} = \sum_{i\ \text{exited in month}\ t} R_i
```

Practical rules:

- Calendar month on the UTC grid. The mark uses the last liquidation-side quote (bid for longs, ask for shorts) of a bar whose **close** time (open time plus period) is at or before the month-end instant. MT5 timestamps are bar open times, so using the open time would look ahead.
- The R unit is the initial risk fixed at entry, so V\_i(t) is comparable across months.
- Entry costs are recognised at entry, the spread through the liquidation-side mark, and exit commission and slippage at the actual exit. Hence V\_i(exit) equals the realised net R\_i, which is what makes the series telescope.
- The price snapshot used for each mark is stored in the ledger, so the observation cannot be revised later.
- A month with no open position and no entry has X\_t = 0. A weekend gap across the month boundary lands in the month in which the next quote falls.

### 1.3 Comparison of the two definitions

| Criterion | X^R: realised only (exit-time assignment) | X^M: liquidation value (adopted) |
| --- | --- | --- |
| Determined by information at month end | Yes | Yes |
| Martingale difference (deviation X\_t minus its conditional mean given the past) | Yes, by construction for any adapted bounded series | Yes, by construction |
| What the conditional mean contains | The expected resolution of positions already open, so it moves with their marks: a large predictable component and strong positive serial dependence in X^R | The expected change in value. Under a martingale price and no costs it is near zero for open positions, so it is closer to drift times exposure minus costs \[T, qualitative, not quantified\] |
| Lag and selective realisation | An open position with a large unrealised loss does not appear until it exits. A lower bound issued at time t can overstate the edge | The unrealised loss is in X\_t at once; no lag |
| Sum over the horizon | Realised P&L of exited positions | Realised P&L plus the unrealised P&L of open positions at T |
| Predictable bounds | Interval \[-N L\_p, N U\_p\] with N at most (open positions at the start of the month + maximum new entries), L\_p and U\_p the per-position bounds on cumulative net R including gaps and costs | Per existing position, the change lies in \[-L\_p - V\_i(t-1), U\_p - V\_i(t-1)\], since V\_i(t-1) is known; a new entry lies in \[-L\_p, U\_p\]. Total width is the same, N (L\_p + U\_p). The location moves with the marks: unrealised gains can be given back, losses already marked leave less downside |
| Gaps | The bound must include the worst gap beyond the stop | Same |
| Specific artefact | None | Month-end quote noise (rollover spread widening, thin liquidity). The price definition is fixed in advance and the bound covers the worst month-end spread |

### 1.4 Effect on the four properties requested

- **Martingale difference.** Both definitions give a martingale-difference deviation, because X\_t is adapted and bounded. The difference is what the conditional mean means, as in the table. The target of E.1 (the running average of conditional means) is therefore closer to an economic expectation under X^M and mixes in more position-carry under X^R.
- **Independence.** The confidence sequence does not need independent observations, and neither definition makes them independent. X^R has built-in serial dependence from carried positions. Under X^M the successive increments of a single position are uncorrelated when the price is a martingale (a stopped martingale has uncorrelated increments), but volatility clustering and the common market factor keep the months dependent. The effect is on how far the target is from the unconditional edge (E.1 caveat), not on the validity of the guarantee.
- **Loss bounds.** Same total width; see the table. The bound must be declared before the month from the open positions at the start of the month and the entry cap, which keeps it predictable.
- **Double counting.** Excluded by the identity below.

### 1.5 The accounting identity and the forbidden hybrid

```latex
\sum_{s \le T} X_s^{M} = \sum_{i\ \text{exited by}\ T} R_i + \sum_{i\ \text{open at}\ T} V_i(T), \qquad \sum_{s \le T} X_s^{R} = \sum_{i\ \text{exited by}\ T} R_i
```

The two series differ only by the unrealised P&L at T. **Double counting arises only in the hybrid** X^bad\_t = (sum of the changes in marks) + (realised R of the positions exiting in the month), which counts each exited position once through its marks and again at its exit. It is forbidden. A mandatory monthly reconciliation compares the running sum of X^M with the ledger's realised P&L plus the marks of open positions; a mismatch stops the confidence-sequence update until resolved.

### 1.6 Which one is used

- **Adopted \[P\]:** X^M for every claim of type 1, 2 and 6 in G.1 and for every lower-bound claim.
- **X^R** is kept only as a descriptive companion series, because of the lag in the table. If X^R is ever used for a claim, the claim must disclose the current unrealised P&L of open positions.
- This is a definition for the text, not one of the six open decisions. It can be overruled; the consequence of choosing X^R instead is the lag disclosure above and a target that includes more position-carry.

### 1.7 Replacement text for V2.2

- **E.1, first sentence.** "Observations X\_t are the monthly change in liquidation value of the strategy's positions (X^M, V2.2.1 section 1): calendar month on the UTC grid, P&L assigned to the month in which it accrues through month-end marks, entry and exit costs included, a month with no open position and no entry recorded as 0."
- **E.2, A1.** "A1. Accounting-closed observations. Each X\_t is determined by information available at the month-end instant, from marks and realised results, and is never revised afterwards. Positions may remain open and enter through their marks. The unit is the calendar month, not the trade: indexed by entry order, trade i's outcome is not known when trade i+1 is entered, so deviations indexed that way are not martingale differences with respect to the entry-order filtration. Indexing by exit order is a different accounting closure that this document does not analyse and does not use."

## 2. Strategy freeze rule during evidence collection

**A confidence-sequence claim belongs to one strategy specification in one environment. Any change to either is either a declared part of the policy (no break), or it ends the old claim and starts a new one. Evidence is never pooled across claims.** \[P\] unless tagged \[T\].

### 2.1 Why a rule is needed: two separate reasons

- **Validity versus meaning \[T\].** A confidence sequence stays a valid statement about the realised stream, even if the strategy changed along the way, provided each change was decided from information available at the time and the bounds stayed predictable. But the statement then concerns a mixture of versions. It is evidence for none of them, and a reader would take it as evidence for the current one.
- **Multiplicity \[T\].** The time-uniform guarantee covers every look at a stream whose start and identity were fixed in advance. It does not cover a start date, a restart, a fork or a variant chosen after seeing results. Reporting the segment that passes is selection and needs its own alpha.

### 2.2 What a claim is bound to

A claim is the tuple: strategy specification hash, environment hash, target definition (X^M, in R per month), threshold delta and direction, alpha share, start month, bounds policy.

- **Strategy specification:** signal logic, parameters, filters, regime labeller, entry and exit rules, risk management (stops, targets, trailing, position caps, daily limits), sizing rule, decision model including its training procedure and weights, instrument and timeframe, execution logic.
- **Environment:** data source, bar construction and time zone, the assumed cost model and the realised-cost accounting, broker or venue, and the definition of X.

### 2.3 Classes of change

| Class | Examples | Effect on the running claim | Required action |
| --- | --- | --- | --- |
| **0. Equivalent change** | Refactoring, logging, dashboards, infrastructure | None, if a replay of the recorded input stream over the whole evidence period reproduces a byte-identical decision and order log | Log the new code hash with the replay-equivalence record. A replay that differs makes it Class 2 |
| **1. Pre-declared adaptation** | Retraining or re-estimation on a declared schedule with a declared algorithm, window, hyperparameters, seed and data cut-off; volatility-scaled sizing by a declared formula; a scheduled parameter switch; a declared drawdown stop | None. The claim is about the adaptive policy as a whole | Conditions P1 to P5 below |
| **2. New strategy version** | Any non-declared change to parameters, filters, thresholds, risk management, decision method (new features, new architecture, off-schedule retraining, hyperparameter re-tuning), regime labeller, instrument or timeframe; a bug fix that alters decisions; a manual override | The old claim ends at the last month in which its rules governed entries. The new version is a new claim | Section 2.5 |
| **3. New environment** | Data source, feed, bar construction or time zone; the assumed cost model; broker or venue; the definition of X | The measured quantity changed even if the strategy did not. Same effect as Class 2 | Section 2.5 |
| **3a. Measurement correction** | An accounting error in how X is computed from the same underlying reality | Not a new claim | Section 2.6 |
| **B. Bounds and bets** | Updating L\_t, U\_t or the betting rule | None, if predictable and the almost-sure containment holds (E.5) | Log the rule; no version change |

**Conditions for Class 1 (P1 to P5).** (P1) The whole adaptation procedure is registered before the claim starts, with a hash of the procedure and of the rules for its inputs. (P2) It uses only data available at the decision time. (P3) Any randomness is seeded and logged. (P4) The almost-sure bounds hold in every state the adaptation can reach. (P5) It is executed exactly as registered; a deviation is Class 2 from the first affected entry. Changing the procedure itself is Class 2.

### 2.4 The five items requested

| Item | Classification |
| --- | --- |
| Code edit | Class 0 if replay-identical, otherwise Class 2 |
| Parameters or filters changed | Class 2; Class 1 only if a declared schedule or rule produced the change |
| Risk management changed | Class 2. Currency-only scaling is Class 0 only if the R series is replay-identical. Lot rounding and minimum lot can change realised R, so equivalence must be shown, not assumed |
| Retraining or change of decision method | Class 1 if it follows the registered procedure exactly, otherwise Class 2 |
| Data source or cost model | Class 3 |

### 2.5 What a new claim requires

1. A freeze date. Evidence for the new claim starts then. Months before the freeze, including those used to design the change, are not evidence for it.
2. Its own alpha share, taken from the reserve (section 3). If the reserve is exhausted, no new inferential claim can start and the new version is reported as descriptive only. Whether to add alpha is part of decision 3 and stays with Ameer.
3. **Changes take effect for new entries only.** A position belongs to the version in force at its entry and runs to its exit under that version's rules. The monthly series of a version is the sum over its own positions. The old claim therefore ends with a run-off period (no new entries), and no month is excluded from either claim, which keeps A5 (no selective omission) intact. A manual override of an open position is a recorded deviation, and its outcome stays in the owning version's series.
4. A bound declared for the new version before its first entry.

### 2.6 Measurement corrections (Class 3a)

An error in the computation of X from the same underlying reality may be corrected, with these conditions: the error is demonstrated by a reconciliation failure (section 1.5) or an independent check, not by its effect on the result; the corrected series replaces the old one for all months uniformly, whatever the direction of the change; the date and reason are logged; claims issued earlier stand as issued with a flag. If the correction moves a claim across its threshold, the claim is withdrawn and re-issued from the corrected series with the same alpha share, recorded as an amendment and not as a restart.

### 2.7 Protection of the evidence

- **E1.** Evidence is indexed by the claim tuple. No pooling, summing or averaging across claims with different specification or environment hashes, and no carry-over of confidence-sequence state, wealth or alpha.
- **E2.** Cross-version tables are descriptive and labelled non-inferential.
- **E3.** A frozen claim keeps its last interval and the alpha it spent. It may be reported later as "version k up to month t" and may not be extended.
- **E4.** A restart or fork of the same strategy is a new claim and charges the reserve. Variants run in parallel (shadow A/B) are separate claims, all counted in the family, including the discarded ones (E.7).
- **E5.** A Class 1 policy remains one claim only while its procedure is unchanged.
- **E6.** Changes take effect at a month boundary where possible. The emergency stop declared in a Class 1 procedure is the exception.

## 3. Alpha reserve: what H recommends, what F.6 computes, and what the reserve costs

**There is no conflict of intent, but the two sections use different bookkeeping. F.6 splits the whole family-wise level 0.10 among the m current strategies, with no reserve. H recommends holding about 20% of that 0.10 (that is, 0.02) back for strategies added later. The recommendation is unchanged; this section only shows its cost.** All figures are \[T\] arithmetic with the formula of F.1 (sigma = sqrt(2) R, 5 trades per month, DE = 1, 80% power, fixed-sample benchmark; a confidence sequence needs more, E.2b).

### 3.1 The two ledgers

```latex
\text{F.6 (no reserve):}\ \alpha_j = \frac{0.10}{m} \qquad\qquad \text{H (reserve } r = 0.20\text{):}\ \alpha_j = \frac{0.10\,(1 - r)}{m},\ \ \text{reserve} = 0.10\, r = 0.02
```

The ledger rule is: the alphas of all claims issued plus the unspent reserve never exceed 0.10. The reserve is split among later additions only when they are registered.

### 3.2 Cost of holding 20% back, for a current family of 1, 3 or 5

Trades needed (years at 5 trades per month) to prove an edge per trade:

| Current family | Reserve | alpha per strategy | 0.10R | 0.20R | 0.30R | 0.50R | Extra data caused by the reserve |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | none (F.6) | 0.100 | 902 (15.0) | 225 (3.8) | 100 (1.7) | 36 (0.6) |  |
| 1 | 20% | 0.080 | 1,010 (16.8) | 252 (4.2) | 112 (1.9) | 40 (0.7) | +12.0% |
| 3 | none (F.6) | 0.0333 | 1,432 (23.9) | 358 (6.0) | 159 (2.7) | 57 (1.0) |  |
| 3 | 20% | 0.0267 | 1,539 (25.6) | 385 (6.4) | 171 (2.8) | 62 (1.0) | +7.5% |
| 5 | none (F.6) | 0.0200 | 1,677 (27.9) | 419 (7.0) | 186 (3.1) | 67 (1.1) |  |
| 5 | 20% | 0.0160 | 1,783 (29.7) | 446 (7.4) | 198 (3.3) | 71 (1.2) | +6.4% |

The percentage is the same for every edge size, because the trades needed scale with (z\_alpha + z\_beta) squared over the edge squared and the edge cancels. The reserve costs most for a family of one and least for a family of five, because a single strategy's level moves from 0.10 to 0.08 while a five-strategy family moves each level from 0.020 to 0.016.

### 3.3 What the reserve buys

The reserve of 0.02, shared among q later additions:

| Later additions q | alpha each | 0.10R | 0.20R | 0.30R | 0.50R |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0200 | 1,677 (27.9) | 419 (7.0) | 186 (3.1) | 67 (1.1) |
| 2 | 0.0100 | 2,007 (33.5) | 502 (8.4) | 223 (3.7) | 80 (1.3) |
| 3 | 0.0067 | 2,200 (36.7) | 550 (9.2) | 244 (4.1) | 88 (1.5) |

Without a reserve, a later addition cannot be accommodated inside a family-wise level of 0.10. A claim already issued at alpha\_j cannot be loosened afterwards, because its confidence sequence was built with that alpha from the start. The alternatives are a second family with its own 0.10 (the project-wide false-claim budget then rises toward 0.20 for two families) or no addition. If the reserve is never used, it is not refunded to existing claims, so the extra data in 3.2 is a sunk cost of keeping the option.

### 3.4 Effect on the other numbers in V2.2

- H row 3 compares m = 3 with m = 10 as 1,432 against 2,007 trades (+40%). That comparison is the no-reserve ledger. With a 20% reserve the same comparison is about 1,539 against 2,113 (+37%) \[T\].
- The 20% figure is a recommendation, not a decision. Whether to hold a reserve, how large, and the family size remain decision 3 and are Ameer's.
- Rounding note: F.6 shows 28.0 years for m = 5 at 0.10R, computed from the rounded 1,677 trades; unrounded it is 27.9, as in 3.2. No conclusion moves.

## 4. Limits of proof for T and S: four different kinds of limit

**V2.2 wrote several sentences about timing skill and regime selection skill in absolute form. They are correct only under V2.2's working conditions, and they mix four kinds of limit that have different causes and different remedies. This section separates them and restates the sentences. It is not a general verdict on every design or market.** \[T\] unless tagged.

**Working conditions of V2.2:** about 60 months of data or fewer, one instrument, regime labels whose episodes last months, about 5 trades per month, confirmatory levels down to 0.00125, and the shift, permutation and surrogate designs described in B.2 and B.3. For the current project this means a VALID window of 24 months and a HOLD window of about 22 months (assumed, not verified).

### 4.1 The four kinds of limit

| Kind | Meaning | Depends on | What would change it |
| --- | --- | --- | --- |
| **(a) Mathematical impossibility (non-identification)** | The estimand cannot be recovered from the observable data at any sample size without added structure | The estimand and the data-generating design, not the sample size | A different design or estimand (a declared baseline; randomisation; exogenous timing) |
| **(b) Insufficient statistical precision** | The estimand is identified, but the sample cannot give the stated power or p-value resolution | Effect size, level, outcome variance, trades per month, design effect, K, and the number of distinct shifts | More months, more independent markets (if their dependence is handled), a higher independent trade rate, a larger effect, a looser level |
| **(c) Insufficient independent episodes** | The information for a regime or timing claim sits in the number of independent episodes or distinct shifts E, not in trades. Floors: 2^-E for a sign test, 1 / C(E, E/2) for a balanced permutation | Episode length relative to sample length; label definition | Faster labels, longer samples, pooling across markets |
| **(d) Invalid assumptions** | The reference distribution needs an assumption known or likely to be false for the design; more data does not help | The design | A design with different assumptions (which then needs its own calibration and class, section C) |

### 4.2 Application to T and S

| Claim and design | (a) Non-identified? | (b) Precision | (c) Episodes | (d) Assumptions | Status under the working conditions |
| --- | --- | --- | --- | --- | --- |
| **T, exogenous timing, shift test** | No | Resolution is about l / T, with l the largest of signal spacing, holding period and volatility persistence. With 1,300 D1 bars and l of 20 to 60 bars the floor is about 0.015 to 0.05; a smaller l lowers it | Distinct shifts, about T / l | Exogeneity holds by design; stationarity assumed | Testable in principle. Level 0.00125 is out of reach with l of 20 bars or more; levels 0.05 and 0.01 are reachable only for the smaller l |
| **T, price-derived signals (breakout, momentum)** | **Yes** for "timing separately from direction" inside one rule, from its own outcomes | Not computed |  | Shift is invalid (timing is a function of the path). Surrogates depend on the null model M0; matched timing depends on the covariates | "The strategy beats M0" or "beats matched random timing given covariates" can be asked and is Uncertified. Separate timing skill is not identified by observational data from that rule |
| **T, randomised entry delay in a shadow run** | No: the effect of a delay of k bars is identified by design | Low for small effects; depends on shadow duration |  | Real randomisation; no interference | Possible only with a shadow run; power not computed \[P\] |
| **S, slow regimes (months), shift or permutation** | No, for a stratified contrast on declared covariates | Contrast is 2.0x to 3.3x harder than an economic test (F.3) | About 20 episodes in 60 months at L = 3 months (10 in, 10 out); 12 balanced independent episodes is **necessary** at level 0.00125, not sufficient (power also depends on the spread of the effect across episodes, which is not computed here) | Label tied to volatility and cost; episodes not exchangeable; stationarity | Not testable at confirmatory levels with about 60 months |
| **S, fast regimes (days to weeks)** | No | Not computed | Episodes in the hundreds for 60 months, so the floor is not the binding limit | Faster labels are more likely to be proxies for volatility or cost, and neighbouring episodes are more dependent | **Not excluded and not tested.** Needs the stratified contrast and a dependence-valid method, and calibration first |
| **S, filter economic value (claim 6)** | No | Same order as claim 1 (F) |  | Closed observations, bounds (E) | Testable at the sizes in F; it is an economic claim, not a skill claim |
| **S, randomised filter on or off by calendar block** | No | Very few blocks, low power |  | Block randomisation, no interference | Possible only with a shadow run \[P\] |
| **Pooling XAUUSD and EURUSD to raise K or E** |  | Helps only if the two are conditionally independent |  | They share the USD factor, so independence is not assumed | Not counted as a remedy until their dependence is modelled and calibrated |

### 4.3 Where V2.2 used the absolute form, and the replacement

| V2.2 location | Original wording | Replacement | Kind |
| --- | --- | --- | --- |
| A, item 3, second bullet (Arabic) | «لا يمكن بعينة تقل عن 5 سنوات وأداة واحدة: مهارة التوقيت أو مهارة اختيار النظام بمستويات تأكيدية. ... وهذا أفضل حالة» | «بشروط العمل في V2.2 (نحو 60 شهراً أو أقل، أداة واحدة، تصنيفات أنظمة بطيئة تقاس بالأشهر، نحو 5 صفقات شهرياً، مستويات حتى 0.00125) لا تكفي الدقة الإحصائية ولا عدد الحلقات المستقلة لإثبات مهارة التوقيت أو اختيار النظام بمستوى تأكيدي. هذا حكم على هذه البيانات وهذه التصاميم، وليس على كل تصميم أو سوق. 12 حلقة مستقلة شرط لازم لا كافٍ. عدم تمييز مهارة التوقيت عن الاتجاه داخل قاعدة واحدة مشتقة من السعر هو حد من نوع (أ) لا يزول بزيادة البيانات» | (b), (c), (a) |
| B.2.3, Resolution bullet | "The level 0.00125 cannot be reached by a shift test on five years of single-instrument data" | "The level 0.00125 cannot be reached by a shift test on five years of single-instrument data when l is 20 bars or more" | (b) |
| B.3.4, last paragraph | "Reaching level 0.00125 therefore needs at least 12 balanced, independent episodes, which is the best case." | "Reaching level 0.00125 therefore needs at least 12 balanced, independent episodes. This is a necessary condition and the best case, not a sufficient one." | (c) |
| B.3.6, last sentence | "A single instrument over five years does not support a confirmatory selection-skill claim." | "With slow regimes, about 5 trades per month and about 60 months, a single instrument does not support a confirmatory selection-skill claim. Faster labels and other designs are not excluded and are untested." | (b), (c) |
| G.1, row 4 (T), last column | "Resolution-limited: p below about 0.015 to 0.05 on five years of single-instrument data for shift tests" | Prefix: "For exogenous timing and a shift test with l of 20 to 60 bars," | (b) |
| G.1, row 5 (S), last column | "Not at confirmatory level with 60 months (contrast is 2.0x to 3.3x harder; episodes needed at least 12, B.3)" | "Not at confirmatory level with about 60 months of slow regimes at 5 trades per month (contrast is 2.0x to 3.3x harder; at least 12 independent episodes are necessary, B.3). Fast labels untested." | (b), (c) |
| I.1, first bullet | "Not a weakness of a particular test: an information limit." | "Under the working conditions of V2.2.1 section 4, this is a limit of precision and of independent episodes in the current data, not a general impossibility. Separate timing skill inside one price-derived rule is a non-identification limit (a). Several shift and permutation designs also rest on assumptions that are likely false (d)." | (a), (b), (c), (d) |

### 4.4 What this does not change

For the current project, XAUUSD and EURUSD on D1 and H4, with the VALID and HOLD windows above, the conclusion of V2.2 stands: no confirmatory claim of timing skill or regime selection skill can be supported. What V2.2.1 removes is the extension of that conclusion to every other design and market. The practical routes to testability are changes of design, not waiting \[P\]: exogenous timing, randomised delay or randomised filter blocks in a shadow run, faster labels with a stratified contrast and a dependence-valid method. Each needs calibration (section D) before it can earn any class in section C.

## 5. Final consistency check of sections B to I after the amendments

**Method and its limit.** I re-read V2.2 sections B to I against each other by searching for the terms that carry the amendments (closed, realised, exit-time, A1 to A6, reserve, family size, 60 months, five years, scenario numbers) and reading each hit in context. This is a targeted consistency check, not a line-by-line proof. Nothing was re-run and no number was recomputed except those listed in 3.4 and in the F.6 rounding below.

### 5.1 Result by section

| Section | Contradictions found | Resolved by V2.2.1 | Remaining |
| --- | --- | --- | --- |
| B (D, T, S validity) | B.1.4 and B.1.5 used "closed" and exit-time language for the CS observation; B.2.3 and B.3.6 absolute wording | Section 1 (terminology), section 4 (wording) | R1 |
| C (classes, methods, assumptions) | C.3 CS row cited A1 to A5 while E has A1 to A6; C.5 "closed" | Section 1 and the change log | R1 |
| D (calibration design) | D.2 row 11 used exit-time monthly analysis; a trade-indexed CS must fail (NC) was not tied to the X definition | Section 1 (X^M, NC defined as entry-order indexed); CS scenario set restated | R2 |
| E (confidence sequences) | E.1 (open positions marked at month end) conflicted with A1 (fully realised); E.9 repeated "closed" | Section 1 (one definition, X^M) | R3, R4 |
| F (power and duration) | F.6 splits the whole 0.10 while H recommends a 20% reserve; one rounding (28.0 should read 27.9) | Section 3 (both ledgers shown); rounding noted | R5 |
| G (claims identity) | G.1 row 1 and G.3 item 3 used "closed"; rows 4 and 5 absolute wording | Section 1, section 4 | none new |
| H (decisions) | Row 3 states +40% without saying it is the no-reserve ledger; the reserve is not priced | Section 3 | R6 |
| I (limitations) | I.1 first bullet states an information limit in absolute form | Section 4 | R5 |

### 5.2 Contradictions and gaps that remain

These are not resolved by clarification. Each needs a decision of yours or a later calibration, or is a scope difference that should be read with care.

| ID | Statement | Why it is not closed here | What would close it |
| --- | --- | --- | --- |
| R1 | The CS bounds L and U (A2) were written per month. With X^M the bound is on the change of liquidation value, which depends on how many positions are open and how far they are from entry. V2.2 gave bet-cap examples (0.0125 vs 0.0080) for the realised definition only | The bound under X^M has the same total width but is not stated as a single number per month for a strategy with overlapping positions | A declared per-position bound and a declared maximum number of simultaneous positions, pre-registered, not computed here |
| R2 | D.2 row 11 asks that the trade-indexed CS fail (NC). With X^M the entry-order-indexed CS is still not a martingale-difference sequence under overlap, but the failure size was never measured, even for the realised definition | The audit did not test any CS; the calibration (section D) has not been run | Calibration scenario 11 |
| R3 | E.1 asserts the CS is valid for the average of conditional means. Under X^M the conditional mean of a month's change includes the marked value of positions entered earlier. Whether the average-of-conditional-means target is the economic target the strategy owner means (profit of the strategy as traded) holds only if every position is eventually closed inside the evidence window or is valued at an unbiased mark | Depends on the mark being unbiased (mid vs bid/ask, the cost of closing, the gap risk of weekends). An open position valued at the last close is not liquidation value | A declared mark rule and a run-off rule (section 2) |
| R4 | E.4 and E.2 (A6) say costs are inside X\_t. Under X^M the exit cost of an open position at the mark must be charged at the mark, or the final month corrects it. V2.2 did not say which | Both choices are valid and give different bounds in the interim months | A decision of yours (accounting rule), pre-registered |
| R5 | All F numbers assume 60 months, n = 5 trades per month, one instrument. The actual windows are 24 months (VALID) and about 22 months (HOLD, assumed). V2.2 says this in places and not in others, so a reader can take the five-year figures for the windows available | This is a scope difference, not an error. F.4 and F.5 show durations in years, which is the correct way to read them | Reading all F tables as "years needed", never as "what VALID can show" |
| R6 | H row 3 recommends about 20% of alpha in reserve. F.6 prices the family with no reserve. Section 3 prices both but does not decide which ledger is used | The reserve share (0%, 10%, 20%) is part of decision 3 (confirmation family size), which stays yours | Decision 3 |
| R7 | Rounding in F.6: 28.0 for m = 5 at 0.10R should read 27.9 (1,677 trades at 5 per month, 60 per year, computed from the unrounded 1,676.6). No conclusion changes | Cosmetic | Edit F.6 on consolidation |

### 5.3 What the check found nothing wrong with

The six-claim identity table (G), the assumption matrix rows other than those listed (C.5), the power tables F.2 to F.5, the corrections to V2.1 (I.2), the calibration rows other than 11, 12, 13 and 14, and the references to the earlier audit \[V\]. These were read for consistency of definitions and cross-references; none was recomputed here, and none was found to contradict another.

## 6. What is unchanged and what stays open

**Unchanged:** all conclusions of V2.2; the earlier audit results, which are not re-described here; v1.2; PR #5 and PR #4 (open, not merged); the registry (20 events, 0 trials, 0 HOLD accesses); the withdrawal of the earlier D and S tests; the position that no D, T or S test is adopted.

**Not done in V2.2.1:** no code, no simulation, no recomputation beyond the arithmetic in 3.4 and the F.6 rounding, no DEV, VALID or HOLD access, no adoption of any test.

**The six decisions remain open and yours:** (1) minimum economic effect in R per month; (2) HOLD end date; (3) confirmation family size, including whether a reserve is held and how large; (4) final calibration envelope; (5) adoption of any statistical test; (6) building shadow execution.

**Proposals introduced here, each open:** the X^M definition and its mark rule (sections 1 and 5.2, R3 and R4); the freeze rule and its change classes (section 2); the claim tuple (section 2). None binds the project until you accept it.

**Literature:** references recalled in V2.2 (Ibragimov and Muller, Dufour, Muller, Howard and Ramdas, Waudby-Smith and Ramdas, Wang and Ramdas, e-BH) are recalled, not re-verified in this round.
