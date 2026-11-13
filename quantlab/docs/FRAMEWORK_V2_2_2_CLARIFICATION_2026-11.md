# QuantLab Framework V2.2.2 — Technical Clarifications Only

2026-11-13 · Ameer

## أ. الملخص (بالعربية)

هذه وثيقة توضيح وتصحيح فقط على V2.2.1. لا كود، لا محاكاة، لا معايرة اصطناعية، لا وصول إلى DEV أو VALID أو HOLD، ولا تعديل على v1.2 أو PR #4 أو PR #5 أو V2.2 أو V2.2.1. لا يُعتمد X^M ولا أي طريقة إحصائية نيابة عنك، والقرارات الستة مفتوحة.

1. **R المجمّع مقابل equity الحساب: محلولة (العيب نفسه).** تعريف V2.2.1 جمع تغيّرات قيمة بوحدات R الخاصة بكل مركز ثم سمّى المجموع "تغيّر equity"، وهذا خطأ في الأبعاد. الحل: تعريف مقياسين منفصلين مع الصلة الدقيقة بينهما: X^R (مجموع R للمراكز، بلا أبعاد، وزن 1 لكل مركز) وX^E = ΔE (عملة). يتطابقان فقط إذا كان r_i ثابتاً لكل المراكز. المقام هو risk_px الفعلي كما في المحرك (يشمل سبريد الدخول وانزلاقه). المقياس المتوافق مع ادعاء "R/month" كما سُمّي هو X^R، لكن اختيار الـ estimand يبقى قرارك.
2. **محاسبة تكلفة التصفية: محلولة جزئياً.** حُدّدت المتطابقات المحاسبية لكل تكلفة بحسب اتفاقيات المحرك (السبريد يُدفع في جهة واحدة: الشراء عند الدخول والبيع عند الخروج)، وقائمة فحص لازدواج العدّ (D1 إلى D8)، والفرق بين قيمة التصفية الفعلية (غير ملاحَظة إن لم تُنفَّذ) وتقدير mark-to-model. لم تُختبر المتطابقات على مخرجات المحرك (لا كود)، وأثر السوق (market impact) مستبعد بافتراض وغير مقاس، وعمولة الوسيط الحقيقية غير مؤكدة.
3. **الحدود المتنبأ بها وصلاحية CS: محلولة جزئياً، مع بند غير محلول.** وُصفت الحدود بدقة: ثوابت يفرضها نظام التداول نفسه (أقصى مراكز متزامنة، أقصى دخول شهرياً، حد أدنى للمخاطرة، سقف الحجم) تعطي حداً شبه مؤكد قابلاً للتنبؤ لكل شهر. طرح التوقع الشرطي يعطي فروقاً مارتينغالية دائماً لأي متتالية قابلة للتكامل، وهذا وحده لا يمنح CS أي صلاحية: يلزم مدى معروف قابل للتنبؤ، ورهانات قابلة للتنبؤ، وتسجيل مسبق، وفهم أن الهدف هو متوسط التوقعات الشرطية لهذا المسار. **غير محلول:** لا يمكن تبرير حد شبه مؤكد لفجوة الخسارة بعد الوقف لمركز CFD من البيانات؛ يبقى افتراضاً مُعلَناً مع بروتوكول كشف بعد الوقوع. البدائل: أداة تحدّ الخسارة تعاقدياً (إن توفرت)، أو CS مشروط بالافتراض، أو CS بعزوم (heavy-tail) بافتراض تباين معلن.
4. **دقة p للإزاحة الدائرية: محلولة جزئياً.** ادعاء "أرضية p ≈ ℓ/T" **مسحوب كادعاء دقة**. الدقة الدقيقة هي 1/T تحت فرضية الثبات الدوري، وصلاحية الاختبار لا تتأثر باعتماد الإزاحات المتبادل (الاعتماد يؤثر على القدرة لا على الحجم). ℓ/T يعمل كتقدير للقدرة القصوى تحت نموذج "هضبة" مبسّط: القدرة القصوى ≈ ⌊αT⌋/ℓ حتى مع أثر لا نهائي. هذا نموذج وليس اختباراً. القدرة تحت بدائل ملساء والمعايرة تحت عدم الثبات تحتاجان معايرة ممنوعة في هذه الجولة.

**ما يتغير في استنتاجات V2.2.1:** صياغة ثلاثة مواضع (تعريف X^M، صف T في §4.2 وما يعتمد عليه، وبعض عبارات §4.3). لا قرار من القرارات الستة تغيّر. ما لا يزال مفتوحاً مسرود في القسم 5.

## Scope, evidence tags and status

**Scope.** Documentation only. No code was written, no simulation or synthetic calibration was run, and no DEV, VALID or HOLD data was touched. Protocol v1.2, PR #4, PR #5, V2.2 and V2.2.1 are not modified; this is a separate document on branch `statistical-audit-2026-11`. All six project decisions stay open (minimum economic effect in R per month, HOLD end date, confirmation family size, final calibration envelope, adoption of any statistical test, building shadow execution). X^M and every method named below are discussed, not adopted. The only project file read in this pass was `docs/COST_MODEL.md`, to align the accounting identities with how the engine charges costs.

**Evidence tags.** Each claim carries one tag, so that intuition is never presented as proof.

| Tag | Meaning |
| --- | --- |
| **[D]** | Derived here: the steps are shown and follow from stated assumptions. Not a machine-checked proof; the reader can verify each line |
| **[H]** | Heuristic or intuition only. No derivation is offered and none should be assumed |
| **[A]** | Assumption that cannot be proved from data and must be declared |
| **[C]** | Read in `docs/COST_MODEL.md` of this project in this pass; not re-tested |
| **[R]** | Recalled from the literature, not re-verified in this pass |
| **[P]** | Proposal. The decision is Ameer's |

**Status of the four issues.**

| Issue | Classification | What is resolved | What is not |
| --- | --- | --- | --- |
| 1. Aggregate R versus account equity | **Resolved** (the defect). One sub-item is a decision | The V2.2.1 wording was dimensionally wrong: it summed quantities in each position's own R units and called the total an equity change. The two measures are different and are now defined separately, with the exact link between them | Which estimand the R/month claim uses is a decision of Ameer. Section 1.6 says which one fits the claim as currently named, and why |
| 2. Liquidation-cost accounting | **Partially resolved** | The accounting identities, the double-counting checks, and the distinction between actual liquidation value and a mark-to-model estimate are specified, using the engine's own conventions [C] | The identities were not tested against engine output (no code, no runs). Market impact is excluded by assumption and is unmeasured. The real broker commission is still unconfirmed |
| 3. Predictable bounds and CS validity | **Partially resolved** | The per-position and per-month bounds are specified exactly, with the conditions under which they are predictable. The role of the martingale-difference identity is stated precisely, and shown to be necessary and far from sufficient | **Unresolved:** no almost-sure bound on gap loss beyond the stop can be justified from data for a CFD position. It remains an assumption with a detect-after-the-fact protocol. The numeric values of the caps are not set |
| 4. Circular-shift p-value resolution | **Partially resolved** | The V2.2 and V2.2.1 statement that the p floor is about l/T is **withdrawn as a resolution claim**. The exact resolution floor is 1/T under the stated null, with a derivation and counterexamples | Power under smooth alternatives and calibration under non-stationarity are unresolved here. They need the calibration that this pass is forbidden to run. The plateau-model power ceiling is a model, not a test |

## 1. Aggregate trade-R versus account equity

### 1.1 What was wrong in V2.2.1

V2.2.1 section 1 defined X^M as "the change in liquidation-value equity over the calendar month", built as a sum over positions of the change ΔV_i, where V_i is the position's value **in units of its own initial risk** (V_i at exit equals the position's realised net R). Each V_i is dimensionless. Its currency value is r_i · V_i, with r_i the position's initial risk in account currency. Adding dimensionless numbers that each use a different currency denominator does not give a currency amount, so the label "account equity" was wrong. The R-unit algebra (telescoping to realised net R, the per-position change bounds) is internally consistent; the defect is the label and the implied claim that the sum equals an equity change. [D]

### 1.2 Notation

Position i has direction d_i, size q_i, entry fill price p_i (including entry spread and slippage), stop price s_i, and value per price unit per unit of size v. Its **initial risk in account currency** is

r_i = q_i · |p_i − s_i| · v.

In the engine, `risk_px` is |fill − stop|, so it **includes entry spread and entry slippage**, and size is computed from it [C]. r_i is fixed at entry and is not revised when a stop is later moved (my proposal for partial closes is in 1.7). The net currency P&L of position i at time t is Π_i(t) (liquidation-valued, see section 2). Its value in R units is V_i(t) = Π_i(t) / r_i. Account equity is E_t; deposits, withdrawals and interest are excluded.

### 1.3 The measures, and the exact link between them

| Measure | Definition | Unit | Weight of position i |
| --- | --- | --- | --- |
| **X^R_t** (aggregate trade-R) | Σ_i ΔV_i(t) | dimensionless | 1 |
| **X^E_t** (equity change) | ΔE_t = Σ_i r_i ΔV_i(t) | account currency | r_i |
| **X^w_t** (reference-risk form) | ΔE_t / r_ref = Σ_i (r_i / r_ref) ΔV_i(t), with r_ref a fixed declared currency amount | dimensionless | r_i / r_ref |
| **X^ρ_t** (equity return) | ΔE_t / E_(t−1) | fraction | r_i / E_(t−1) |

Identities [D]:

- X^E = r_ref · X^w. If r_i = r_ref for every position, then X^w = X^R. This is the only case in which the trade-R sum and the equity change are proportional.
- With sizing at a fixed fraction f of equity at entry, r_i = f · E_(τ_i). Then X^ρ_t = f · Σ_i (E_(τ_i) / E_(t−1)) ΔV_i. The weights differ from 1 whenever equity moved between the month's start and the entry of the position, including entries inside the month. So X^ρ is not f · X^R even with constant f.
- X^R − X^w = Σ_i (1 − r_i / r_ref) ΔV_i. Its expectation is a covariance-type term between sizing and conditional expected R. It is zero when sizing does not vary, or when conditional expected R is the same for every position, and not otherwise.

### 1.4 Effect of variable sizing

1. **Under the null of zero expected R per position, validity does not depend on sizing.** If every position has conditional expected ΔV equal to zero, any predictable weights give zero expected X. Sizing only changes the bounds (section 3), not the null. [D]
2. **Under an alternative, the measures estimate different things.** X^R is the per-unit-risk R summed over positions and is independent of the sizing rule. X^w and X^E weight positions by their size, so an edge concentrated in small positions is diluted, and an edge in large positions is amplified. If sizing is correlated with expected R, X^R and X^w target different quantities. [D]
3. **Equity-proportional (compounding) sizing makes the weights grow with equity.** The conditional mean of X^ρ then depends on the equity path, and a confidence sequence for the average conditional mean mixes months with different scale. No fixed numeric bound exists without a cap on the weights. [D]
4. **Lot rounding makes realised risk differ from target risk.** The project notes record that at the minimum lot of 0.01, wide gold stops either exceed the target risk or are rejected (a typical D1 stop gave about 0.33% realised risk against a 0.5% target). So r_i varies across positions even under "fixed fractional" sizing, and r_i is correlated with the stop width, which may correlate with outcomes. [H] as to the size of the correlation; the variation itself is documented in the project notes.

### 1.5 Effect of overlapping positions

- X^R counts each position once. A month with three simultaneous positions contributes up to three R-units of exposure. The monthly total therefore depends on the trade-frequency policy (the cap on simultaneous positions) as well as on the per-position edge. Two strategies with the same per-position edge and different caps have different R per month. Comparisons across strategies must hold the policy fixed. [D]
- Overlapping positions in one instrument and direction have strongly correlated ΔV_i (same price path). This raises the variance of X^R above n times the per-position variance and widens the worst-case bound. It does not change the estimand. [H] for the size of the effect; the sign is not in doubt.
- X^E adds the currency P&L of overlapping positions without further definition. X^R needs the conversion factor to equity: three simultaneous stop-outs are −3R, which is 3f of equity if each position risks fraction f. The R unit is the right unit for heat-weighted P&L and the wrong unit for statements about account percentage. [D]

### 1.6 Which definition fits the R/month claim

The claim as named in V2.2 (section F and the first row of G.1) is "average monthly net R of the strategy as traded, at a named cost model". "R" means per unit of **initial risk of each position**, so the quantity summed is X^R. It does not depend on account size or on compounding, and it is the quantity the V2.2 power tables assumed (outcome sd of about √2 R per trade, about five trades per month). The equity measures answer a different claim ("how much does the account grow per month, in currency or in percent"), which depends on the sizing policy and starting equity. That claim would need its own target, its own weights and cap, and its own power tables. [D]

So, for the claim **as currently named**, X^R is the consistent definition. I propose [P] to call it "aggregate liquidation-valued trade-R", to stop describing it as account equity, and to keep the equity-based claim, if wanted, as a separate claim outside the six-claim table. X^R is also the only one of the four with weights that need no cap for the bounds in section 3. The choice is Ameer's. Two limits must be stated with it:

- X^R describes the strategy at unit risk. The account as actually traded may earn differently if its sizing rule is correlated with expected R. X^R does not capture that. [D]
- Nothing here shows that either definition has an economically meaningful minimum effect. That is decision 1 and stays open.

### 1.7 Denominator and aggregation, stated precisely

- **Denominator:** r_i = q_i · risk_px_i · v, with risk_px_i = |entry fill − stop| including entry spread and slippage, fixed at entry [C].
- **Aggregation for X^R:** X^R_t = Σ over positions with any life in month t of ΔV_i(t). Equal weights. Empty month = 0.
- **Partial closes and scale-ins [P]:** each fragment keeps its pro-rata share of r_i. I did not verify how the engine treats partial closes; treat this as an unverified assumption [A].
- **Lifetime consistency [D]:** summed over a position's life, ΔV_i equals its net R, which is the engine's `net_R = (net price profit − commission − swap) / risk_px` [C]. This holds exactly only because the mark estimate is replaced at exit (section 2.4).

**Classification of issue 1: Resolved** (the defect; the equity measures are now separate and defined). **Open for Ameer:** the choice of estimand and of r_ref if a weighted claim is wanted.

## 2. Complete liquidation-cost accounting

### 2.1 What the engine does [C]

- Price data are **bid** bars. A long enters at Ask + L_in = bid-open + spread + L_in. A short enters at Bid − L_in. The spread is paid **once per round trip and on one side only**: for a long at entry (through the Ask), for a short at exit (through the Ask).
- Long stop-out: triggers when Low ≤ stop (Bid), executes at stop − L_out. Short stop-out: triggers when High + S ≥ stop (Ask), executes at stop + L_out. Target fills are limit orders without slippage. Time exits fill at Close − L_out (long) or Close + S + L_out (short). A stop that gaps executes at the worse opening price.
- Effective spread per bar e = max(measured, floor) × scenario multiplier: the floor **replaces** the measured spread and is not added to it.
- Commission is a fixed amount per lot for the round trip (converted to price terms) and is charged **once per trade**. Swap is nights × points, charged with Wednesday counted three times. Slippage is a fixed price amount at entry and at stop or time exits, none at limit targets.
- `risk_px` includes entry spread and entry slippage. A stop-out with spread only is **exactly −1R**. Commission, exit slippage and swap show as a loss larger than 1R.

### 2.2 Cost components and where each enters

| Component | Where it enters | Allocation in the engine [C] | In R units | Double-counting risk and rule |
| --- | --- | --- | --- | --- |
| Entry spread | Inside the entry fill (long: Ask) | Paid at entry for longs; for shorts the spread appears at exit | Inside `risk_px` for longs | Do not subtract again as a separate cost when profit is computed from fills |
| Exit spread | Inside the exit fill (short: Ask) | Paid at exit for shorts; for longs it was paid at entry | Part of the price profit | Same rule. The floor replaces the measured spread, never adds to it |
| Entry slippage | Inside the entry fill | Fixed price amount | Inside `risk_px` | Do not add a modelled amount where a fill price is observed (live) |
| Exit slippage | Inside the exit fill (stop and time exits only) | Fixed price amount | cost / `risk_px` | None on limit targets; do not add on top of a gap fill unless declared (see D8) |
| Entry commission | Cash charge | Engine: none separately; the round-trip commission is deducted once at the end of the trade | cost / `risk_px` | Real MT5 accounts usually charge at each deal. Whatever the split, entry plus exit must equal the round-trip amount once |
| Exit commission | Cash charge | Same | same | Same |
| Swap | Cash accrual per night | Accrued nights × points | cost / `risk_px` | Accrue to date in a mark; the total at exit replaces the accrual, never adds to it |
| Market impact | Price move caused by the order | **Not in the engine** | not modelled | Excluded by assumption (2.6) |
| Month-end liquidation cost | Counterfactual exit cost of a position still open | **Not in the engine; it is a mark estimate** | estimate / `risk_px` | Estimate in the mark, replaced at actual exit (2.4) |

### 2.3 Double-counting checks

Each of the following is a way to count a cost twice. Each is stated with the rule that prevents it. None was tested against engine output in this pass.

- **D1. Spread inside the fills and again as an explicit deduction.** Profit computed from fill prices already contains the spread. The engine's `spread_px` column records the embedded spread; it must not be added to the profit as a further cost. [C]
- **D2. Floor added to the measured spread.** The engine uses max(measured, floor). [C]
- **D3. Commission at entry and again at exit.** If the real broker charges a round-turn amount at entry, the exit estimate in a mark must be zero. If it charges half on each side, the mark carries only the remaining half.
- **D4. Side asymmetry in marks.** Under the engine's convention a long's mark at Bid already is the executable exit price and the entry spread is already paid, so adding the spread again in the mark double counts. A short's mark at Bid understates the exit price, which is Ask = Bid + e, so the spread not yet paid must be added once. The mark is therefore asymmetric by side. [D from C]
- **D5. Estimate plus actual.** The month-end estimate of the closing costs and the actual closing costs must **replace** each other in the exit month's increment (V at exit minus V at the previous mark). Adding the actual costs on top of an earlier estimate double counts.
- **D6. Two denominators.** The engine's cost-in-R divides by `risk_px`, which includes entry spread and slippage. Mixing it with a gross-stop-distance denominator in another place (a bound, a table) double counts the entry costs.
- **D7. Swap accrued in a mark and again at exit.** The exit total replaces the accrual.
- **D8. Gap exits.** The engine executes a gapping stop at the worse opening price. The documentation does not say whether the stop-exit slippage L_out is also added on top. This is **not verified**. If it is added, the gap exit is charged slippage on a price that already includes the gap.

### 2.4 Lifetime identity and why the month-end mark redistributes without adding [D]

For an open position at time t, define the mark

V_i(t) = [ d_i · (X̂_i(t) − X_i^entry) − Ĉ_i(t) − Ŵ_i(t) ] / risk_px_i,

per unit of size, where X̂_i(t) is the declared executable-side exit price estimate (long: Bid minus the declared exit slippage allowance; short: Ask plus the allowance), Ĉ_i(t) the pending commission, Ŵ_i(t) the swap accrued to t, and X_i^entry the actual entry fill. At the actual exit, V_i equals the net R of the trade, with all costs actual. Before entry, V_i = 0.

- A freshly entered long has V = −(e + L_in + allowances) / risk_px: the value just after entry is minus the immediate round-trip cost. A freshly entered short has the same by symmetry (−L_in − e − allowances). So the entry month's increment carries the entry costs and the expected exit costs. [D]
- The monthly increments ΔV_i(t) sum over the position's life to V_i(exit) − 0 = its net R, whatever the estimates in the intermediate marks were. The marks move value **between months** and cannot change the lifetime total. [D]
- Corollary: when the evidence window ends with positions still open, the last month contains marks, not realised values, for those positions. The claim is then "net R including a mark for open positions". To avoid it, the window can end when the account is flat, or run-off rules can attribute open positions to the version that entered them (V2.2.1 section 2). [P]

### 2.5 Actual liquidation value versus mark-to-model

- **Actual liquidation value at t:** the net R that would be realised if the position were closed at the first executable opportunity after t. It depends on the spread at that moment, the slippage draw, and any gap before the next tradable quote. A month ending on a Friday close means the first opportunity is after the weekend gap. It is a **random variable not known at t**, and if the position is not actually closed it is **counterfactual and never observed**. An observation cannot be defined on an unobserved counterfactual.
- **Mark-to-model:** the value computed by a **pre-declared rule known at t**: the executable-side last price at the month-end bar close (using the bar close time, since MT5 bar timestamps are bar opens), the engine's effective spread rule for the side, declared exit slippage allowance, pending commission, and accrued swap.
- The two are **not identical**. The difference has a conditional mean (the bias of the allowance) and a random part (the actual spread, slippage and gap). No claim is made that the mark is conditionally unbiased for the actual liquidation value. [A]
- Consequences. (i) X^M must use the mark, never the actual liquidation value. (ii) The claim is conditional on the cost model **and** the mark rule, and both must be declared before the window. (iii) In the position's exit month the increment absorbs the difference between the actual exit and the earlier mark, so the **bounds in section 3 must cover that difference**. (iv) If the strategy actually liquidated everything at each month end, it would be a different strategy (forced monthly liquidation) and the counterfactual would then be real. That is a decision about the strategy, not a measurement choice.
- The month-end spread can be unrepresentative (rollover and weekend widening). The mark rule must say which spread it uses (the engine's effective spread rule is the default candidate) and must not be tuned after the data are seen. [P]

### 2.6 Market impact

Market impact is not in the engine and is excluded here **by assumption [A]**: the strategy is a price taker at sizes up to a declared q_max, for which a retail demo account in XAUUSD and EURUSD shows no measurable impact, and nothing in the project's data can measure impact. The cost of liquidating several positions at once at a month end is not modelled. The claim therefore does not transfer to larger sizes. If impact were included it would add a size-dependent term to the closing-cost estimate. It is unmeasured.

### 2.7 What was and was not done

Specified here: the identities in 2.2 to 2.5, the eight double-counting checks, and the distinction between actual and marked value. **Not done** (no code and no runs): comparing the sum of monthly ΔV_i with the engine's `net_R` for every trade, checking the side asymmetry of marks, resolving D8, and confirming the real broker's commission timing and amount (7 USD per lot round trip is still a provisional assumption). These are a pre-registered verification list for a later, separately approved step, not results. [P]

**Classification of issue 2: Partially resolved.** The accounting is specified; verification against the implementation and the broker is not done, and market impact is excluded by assumption.

## 3. Predictable bounds and confidence-sequence validity (R1 expanded)

### 3.1 Setting and invariants

Months t = 1, …, K. F_t is the information through the month-end mark of month t. The bounds use only F_(t−1) and rules the strategy **enforces by construction**. Declared invariants:

- **I1.** At most N_max positions open at once.
- **I2.** At most n_new entries in any calendar month.
- **I3.** Every entry has `risk_px` at least ρ_min (the stop is never tighter than ρ_min), and size at most q_max.
- **I4.** For a weighted measure: weights w_i in [0, w_max]. For X^R, w_i = 1 and I4 is not needed.
- **I5.** An exit guarantee (stop, plus a time stop or target) so that no position stays open without bound.

Declared allowances, which are **assumptions [A]**: c̄ (maximum commission, swap and exit slippage per unit of size, in price terms), Γ (maximum adverse price gap beyond the stop at execution) and Γ′ (maximum favourable gap beyond a target). A take-profit at distance T_i gives an upper bound on the favourable side; a strategy with no target has no upper bound at all.

### 3.2 Per-position bounds [D, given the allowances]

While a position is open and has not been stopped, the executable price at the mark is still on the safe side of the stop: for a long, Low > stop, so Close > stop; for a short, High + S < stop, so Close + S < stop. Hence

V_i(t) ≥ −1 − (L̂_out + Ĉ + Ŵ) / ρ_min  while open,

and at exit

V_i(exit) ≥ −ℓ, with ℓ = 1 + (c̄ + Γ) / ρ_min,
V_i(exit) ≤ u, with u = RR_max + Γ′ / ρ_min  (RR_max the largest declared target multiple; costs only reduce it).

The costs and the gap enter divided by ρ_min: **bounding R requires a floor on the stop distance**. With a tight stop, a fixed cost or gap is a large number of R. Illustrative arithmetic only, with invented values chosen to show the formula and not estimates: c̄ = 0.5 and Γ = 10 price units with ρ_min = 10 give ℓ = 1 + 1.05 = 2.05 R.

### 3.3 Monthly bounds [D, given I1 to I3 and the allowances]

For month t, ΔV_i(t) = V_i(t) − V_i(t−1), where V_i(t−1) = 0 before entry and V_i(t−1) = V_i(exit) after exit (increment zero).

- **Positions open at the end of month t−1** (set O, known at F_(t−1), |O| ≤ N_max): ΔV_i ∈ [−ℓ − V_i(t−1), u − V_i(t−1)]. The endpoints are F_(t−1)-measurable because V_i(t−1) is.
- **Positions entered during month t** (at most n_new, not known at F_(t−1)): ΔV_i = V_i(t) ∈ [−ℓ, u], the same bounds.

Hence X^R_t lies in [−L_t, U_t] with

L_t = Σ_(i∈O) (ℓ + V_i(t−1)) + n_new · ℓ,
U_t = Σ_(i∈O) (u − V_i(t−1)) + n_new · u,

and the width U_t + L_t = (|O| + n_new)(ℓ + u) ≤ (N_max + n_new)(ℓ + u). This also covers positions carried across month boundaries. A position that opens and closes inside the month is counted in n_new. The invariant I2 is what makes the entry count bounded; I1 alone does not, because positions can open and close repeatedly. For a weighted measure the same bounds apply with each term multiplied by w_max.

### 3.4 When the bounds are genuinely predictable and valid

All of the following must hold. If any fails, the almost-sure claim fails.

1. I1 to I3 (and I4 if used) are **enforced in the order-submission logic** and cannot be bypassed by a manual override, a bug, or a broker partial fill that changes the size or the stop. Enforcement must be logged.
2. The allowances c̄, Γ and Γ′, the mark rule, ρ_min, N_max and n_new are **declared before the window** and not tuned after seeing X.
3. The bound functions use only F_(t−1) (for example V_i(t−1)), never later information.
4. The bets in the confidence sequence are F_(t−1)-measurable.
5. Changing any of I1 to I5, the allowances, or the mark rule is a change of class in the freeze rule (V2.2.1 section 2), not a silent update.

**Variable sizing.** With compounding sizing the weights grow with equity and no fixed numeric bound exists unless a cap w_max is enforced; with a cap the formulas above hold. For X^R the weights are 1 and sizing does not enter the bound, which is a practical reason, besides the one in 1.6, to prefer it. Lot rounding does not affect X^R's bounds, because r_i is the realised risk, but I3 must be stated on realised `risk_px`.

### 3.5 Gap risk: no defensible almost-sure bound from data

Γ is the largest adverse jump past a stop at execution. For a CFD position with a market-order stop, no contract and no finite sample limits it. The largest observed gap in a data set is a lower bound on the true maximum, and heavy-tailed jump distributions mean no sample size makes the sample maximum an upper bound. Extreme-value estimates give a number with its own uncertainty [R]. So:

**The almost-sure bound is conditional on an assumption about Γ that cannot be proved from data, and the bound is therefore not defensible as a proven bound.** Design can enforce caps on exposure (N_max, n_new, ρ_min, q_max) but not on price. The breach protocol of V2.2 (declare a breach whenever X_t < −L_t, freeze every claim using that month, record the true loss) detects a violation after it has happened. It does not prevent one, and after a breach the confidence sequence is not valid for the periods that used the broken bound.

### 3.6 Why subtracting the conditional expectation gives martingale differences, and why that is not enough

Let m_t = E[X_t | F_(t−1)], which exists when X_t is integrable (guaranteed by the bounds above) and is F_(t−1)-measurable. Define D_t = X_t − m_t. Then

E[D_t | F_(t−1)] = E[X_t | F_(t−1)] − E[m_t | F_(t−1)] = m_t − m_t = 0,

because m_t is known given F_(t−1). [D] So (D_t) is a martingale-difference sequence **by construction, for any integrable adapted sequence**: fat-tailed, dependent, unbounded or not. An identity that holds for every such sequence carries no information about this one. What it does not give:

1. **A range or tail condition.** Confidence-sequence constructions need D_t, conditional on F_(t−1), to lie in an interval of known predictable width, or to satisfy a sub-Gaussian-type bound with a predictable variance process [R]. With the bounds of 3.3, D_t lies in an interval of known width c_t = U_t + L_t (the location is unknown because m_t is), and Hoeffding's lemma gives E[exp(λ D_t) | F_(t−1)] ≤ exp(λ² c_t² / 8) [D, from the lemma]. This is what the range-based sequence of V2.2 uses. Without an almost-sure bound the identity yields nothing quantitative. A Chebyshev-type sequence needs a known conditional variance bound instead.
2. **A fixed target.** The sequence covers the average of the unobservable conditional means, (1/n) Σ m_t, **for this path**. The m_t can vary with F_(t−1) (regime, volatility) in any way. Reading it as "the strategy's true edge" needs a stationarity assumption on m_t that is not part of the construction. [D]
3. **Free handling of dependence.** Dependence between months is absorbed into m_t, so it does not invalidate the construction, but it does not make the width small either: the width depends on the predictable range, and persistence in m_t makes the target path-dependent. [D]
4. **Pre-specification.** The bets, the boundary, the stopping rule, the strategy version and the bounds must be fixed in advance. A time-uniform guarantee holds for one pre-specified sequence under one filtration; choosing among several sequences after looking breaks it even though each is valid alone. [D]
5. **A usable width.** The range-based width is driven by (N_max + n_new)(ℓ + u) per month, which with the illustrative numbers above is of the order of several times the realistic monthly standard deviation. Validity is not the same as power. Variance-adaptive constructions use the empirical variance but still need the bound. [H] as to the size; V2.2 section E.2b already gave an explicit example.

One more caution, to prevent a tempting simplification. For a null in which **each** conditional mean is at most m, the process W_t = Π (1 + λ_s (X_s − m)) with predictable λ_s in [0, 1/(L_s + m)] is a nonnegative supermartingale, so only the loss bound is needed for that test. [D] But rejecting "each conditional mean ≤ m" is easier than rejecting "the **average** of the conditional means ≤ m", because the first null is smaller. A path with some good and some bad months can reject the first without the average being above m. That test must not be used to certify an average. Whether a one-sided construction with only the loss bound exists for the average target is **not established here**.

### 3.7 If no defensible almost-sure bound exists: what would be required

Stated plainly: for gap loss on a CFD position, none can be established. The options, each needing a decision by Ameer:

1. **Assumption with a breach protocol** (current V2.2 design). The sequence is valid conditional on the declared Γ. The claim must carry the label "conditional on the bound assumption". [A]
2. **A contractual cap on loss** (a guaranteed stop-loss order or a purchased option hedge) so that Γ is limited by the instrument. Availability on the project's brokers is not established, and the cost would enter the net R. [A]
3. **A moment-based sequence** that replaces boundedness by a declared bound on a conditional variance or a higher moment (for example truncation or Catoni-type constructions for heavy tails) [R, not verified here]. It rests on a different assumption, also unprovable from data, and gives wider intervals.
4. **State the result as a stress claim:** the claim holds at declared gap allowance Γ, with separate reporting of observed gaps. This does not remove the assumption.

The numeric values of N_max, n_new, ρ_min, q_max, w_max, c̄, Γ and Γ′ are not set here. They belong to the strategy definition and to the calibration envelope (decision 4).

**Classification of issue 3: Partially resolved.** Resolved: the specification, the predictability conditions, the role of the martingale-difference identity. **Unresolved:** a defensible almost-sure bound for gap risk; the numeric caps; whether a loss-bound-only construction exists for the average target.

## 4. Circular-shift p-value resolution

### 4.1 What V2.2 and V2.2.1 claimed, and what is being re-examined

They stated that the number of effectively distinct shifts is about T / ℓ, with ℓ the largest of the signal spacing, the holding period and the volatility persistence length, and that the smallest attainable p is about ℓ / T: 0.015 to 0.05 for T near 1,300 and ℓ from 20 to 60 bars. They concluded that level 0.00125 cannot be reached. That equated an effective-sample-size idea with p-value resolution without justification. This section separates the concepts.

### 4.2 Setup

The data are a series y_1, …, y_T (returns or the price path), treated as lying on a circle. The signal vector s is fixed (exogenous). For a shift k, s^(k)_t = s_(t−k mod T). The statistic is S_k = f(s^(k), y), for example the mean outcome at signalled bars, with each outcome computed from the path with the declared exit rule on the wrapped path. The observed value is S_0. The counting p-value is

p = (1 + #{k in 1..T−1 : S_k ≥ S_0}) / T.

**Null H_c [A]:** the law of y is invariant under cyclic shifts, that is (y_(1+j), …, y_(T+j)), indices mod T, has the same law as y for every j. Also f is shift-equivariant: shifting s and y together leaves f unchanged (false if f depends on the absolute alignment, for example time of day, unless shifts are multiples of the cycle). Under these, S_k = f(s, y shifted by −k).

### 4.3 Claim 1: exact validity and resolution 1/T [D]

Under H_c, for every j in 1, …, T, P(p ≤ j / T) ≤ j / T. If all S_k are distinct, p is uniform on {1/T, 2/T, …, 1}. In particular p = 1/T is attainable, and the test is valid at every level α ≥ 1/T, **however strongly the S_k are correlated with each other**.

Derivation. The cyclic group G acts on y. Write S(y) = f(s, y) and consider the orbit values S(g_k y), k = 0, …, T−1. Under H_c, g_j y has the same law as y for every j, and the orbit of g_j y is the same multiset as the orbit of y. Condition on that unordered multiset. The observed S(y) is the element at position 0, and since y and g_J y share law and orbit, the position of the observed value in the orbit is uniform over the T group elements (the action is free for a continuous y). So the rank of S_0 is uniform, and counting ties as ≥ makes the p-value conservative. This is the standard randomisation-test argument (Hoeffding 1952; Lehmann and Romano) [R for the theorem; the outline above is [D]]. Nothing in it uses the correlation of the S_k.

Therefore: **dependence between the S_k does not enter validity or the granularity of p.** The notion of "effective number of independent shifts" is irrelevant to both.

### 4.4 Total, distinct, independent: three different counts

| Count | Value | Meaning |
| --- | --- | --- |
| Total transformations | T | The group order |
| Distinct transformations | at most min(T, number of distinct signal vectors, number of distinct statistic values) | What limits the resolution |
| Independent or weakly dependent shifts | about T / ℓ [H as to "about"] | A statement about the correlation of S_k, not about resolution |

Counterexamples to "T shifts give 1/T":

- **Periodic signals.** If s has period P (for example "every fifth bar", a weekday signal on D1), only P distinct signal vectors exist, each repeated T/P times, and the floor is 1/P. For P = 5 the floor is 0.2 at any sample size. Near-periodic calendar signals (month-start dates of unequal length) give near-ties in the same way. [D]
- **Discrete statistics.** A hit-rate over m events takes at most m + 1 values; the number of shifts that reach the maximum can be large, and ties count as ≥, so the floor is that number divided by T and not 1/T. A continuous statistic (mean R) has no ties with probability one. [D]

### 4.5 Where the neighbourhood effect comes from, and why it is not a resolution floor

Take an additive-window statistic: the outcome of an event is the sum of h consecutive bar returns starting at the event, and S_k is the mean over events. With iid returns of variance σ² per bar and events separated by more than h + |k|, cov(Y_j, Y_j^(k)) = σ² (h − |k|)^+ and var = h σ², so

corr(S_0, S_k) = (1 − |k| / h)^+.

Shifts within h bars of 0 are strongly positively correlated with S_0, and shifts further away are uncorrelated. This is where "T / ℓ approximately independent shifts" comes from. [D for this model]

It matters for **power**, not for resolution. **Plateau model [A]:** under an alternative with an effect e at a single bar inside the window (the first bar after the signal), the shifts that still cover that bar form a plateau of ℓ = h shifts with the same mean, and in the large-effect limit every shift outside the plateau falls below every shift inside it. Within the plateau the S_k differ only by noise, so the rank of S_0 among the plateau is approximately uniform on 1, …, ℓ. Then p = rank / T and

P(p ≤ α) = min(1, ⌊αT⌋ / ℓ),

**even with an infinite effect size**. This is a power ceiling, not a p-value floor. The median attained p is about ℓ / (2T) and the minimum 1/T is attained with probability about 1/ℓ.

Numbers for T = 1,300 (αT = 1.625, so ⌊αT⌋ = 1): ceiling 1 for ℓ = 1, 5% for ℓ = 20, 1.7% for ℓ = 60, all at α = 0.00125. For the 24-month VALID window, T is about 500 D1 bars: 1/T = 0.002 is already above 0.00125, so level 0.00125 is out of reach **by resolution alone** on daily bars. Both statements are [D] **under the plateau model, which is a simplification and has not been tested by simulation**.

Counterexample to the claim that ℓ is a property of the data length or of "volatility persistence": a statistic that uses only the return of the bar after the signal has a plateau of width 1, so ℓ = 1 and the ceiling is 1 whenever ⌊αT⌋ ≥ 1. The plateau width ℓ belongs to the **statistic and the alternative**. Neither signal spacing alone nor volatility persistence sets it: signal spacing matters only when events are closer than h, and volatility persistence changes the variance of S_k across k (heavier orbit tails, harder to beat) without creating a plateau [H].

Finer bars do not remove the ceiling: T grows by the bar-count factor and ℓ (the same calendar plateau) grows by the same factor, so ⌊αT⌋ / ℓ is approximately invariant except for the rounding. [D, trivial]

### 4.6 Calibration under dependence

Exact under H_c for any dependence inside y, including autocorrelation and stationary volatility clustering (4.3). The earlier synthetic audit found the shift reference nominal under the nulls it tested [V], consistent with this. **Invalid** when H_c fails:

- **Non-stationarity or a wrap-around jump.** A trend or level shift makes the join between y_T and y_1 unrepresentative. [H] for magnitude.
- **Events concentrated in a particular regime** (endogenous signals): S_0 has a different variance from the typical shifted S_k, so P(S_0 is extreme) departs from nominal. For a mean-return statistic with events in a high-volatility cluster the direction of the error is over-rejection by a variance argument; the size is not computed. [H]
- **A non-equivariant statistic** (time-of-day, session or month-end alignment).
- **A signal that depends on the path** (breakout, momentum): the shifted signals are not draws from the same law as the observed one.

These are the (d) assumptions of the four-way taxonomy of V2.2.1 section 4. They are conditions about the design, and more data does not remove them.

### 4.7 Scope of this correction

The counts 1 / C(E, E/2) for permutation tests of episode labels are exact counts of distinct balanced labelings and remain a legitimate resolution floor under exchangeability of episodes, which V2.2 itself called doubtful. They are unaffected here except that the "needs at least 12 episodes" statement stays a **necessary** condition (already amended in V2.2.1 section 4.3). For circular shifts of regime labels, the analysis of this section applies.

### 4.8 What this changes in the T conclusion

V2.2.1 section 4.4 said the conclusion of V2.2 stands. After this section it stands **for a different reason and with a different status**:

- The statement "the level 0.00125 cannot be reached by a shift test because the resolution is l/T" is **withdrawn**. The resolution is 1/T.
- What remains is a power ceiling under the plateau model, about 5% at α = 0.00125 for a 20-bar plateau on 1,300 bars, a **model** and not a proof, and a resolution limit that is real only for very short windows (24 months at daily resolution).
- A short-plateau statistic is **not excluded** and has not been tested. Price-derived signals remain non-identified for separate timing skill (V2.2.1 section 4.2, kind (a)).
- So "no confirmatory timing claim can be supported with the current windows" is **not demonstrated by the resolution argument**. It rests on the plateau-model ceiling and on the design assumptions. The honest status is: not shown possible, not shown impossible, with the evidence leaning to impossible for long plateaus.

**Classification of issue 4: Partially resolved.** Resolved: the resolution claim (1/T under H_c, with counterexamples and a derivation). **Unresolved:** power for smooth and mixed alternatives, calibration under non-stationarity, and the plateau model itself, all needing the synthetic calibration this pass may not run.

## 5. Corrections to V2.2 and V2.2.1, and what remains open

### 5.1 Corrections (V2.2 and V2.2.1 are not edited; these supersede the listed passages)

| # | Location | Change | Reason |
| --- | --- | --- | --- |
| 1 | V2.2.1 section 1 (1.1 to 1.7) and V2.2 E.1 | X^M renamed "aggregate liquidation-valued trade-R" (X^R). "Change in account liquidation-value equity" removed. The equity measures are defined separately (1.3) | Dimensional inconsistency |
| 2 | V2.2.1 section 1, denominators and bounds | The R denominator is the engine's `risk_px` (entry fill to stop, including entry spread and slippage), not a gross stop distance | Mixed denominators double count entry costs (D6) |
| 3 | V2.2.1 section 1, mark rule | Marks are asymmetric by side under the engine's convention (D4); actual liquidation value is not an observable (2.5) | Double-counting risk and an unobservable counterfactual |
| 4 | V2.2.1 section 5.2, R1 | Expanded to sections 3.1 to 3.7. R3 and R4 specified in 2.4, 2.5 and 2.7; their decisions remain open | The request |
| 5 | V2.2 E.2 (A2, bounds) | The almost-sure bound requires invariants I1 to I3 (I4 for weighted measures) and declared allowances; the gap allowance is an assumption | Gap risk cannot be bounded from data |
| 6 | V2.2 B.2.3 (resolution bullet), V2.2.1 section 4.2 (T row), V2.2.1 section 4.3 (row for B.2.3), V2.2 G.1 row 4 | "Resolution about l/T, p floor 0.015 to 0.05" withdrawn as a resolution claim. Replacement: "resolution 1/T under cyclic invariance; power ceiling min(1, floor(alpha T)/l) under a plateau model, not tested" | Section 4 |
| 7 | V2.2.1 section 4.4 and V2.2 I.1, first bullet | The T conclusion is restated as "not shown possible, not shown impossible", with the evidence leaning against long plateaus | Section 4.8 |

No conclusion about the six decisions moves, and none of the F tables is changed.

### 5.2 Remaining open items

- **O1.** The choice of estimand (X^R or a weighted measure, and r_ref) is Ameer's.
- **O2.** The verification list in 2.7 is not done, and D8 is unresolved.
- **O3.** The numeric caps and allowances (N_max, n_new, ρ_min, q_max, w_max, c̄, Γ, Γ′) are not set.
- **O4.** No defensible almost-sure gap bound exists; options 1 to 4 in 3.7 are Ameer's to choose among.
- **O5.** Power and calibration for the shift test under non-stationarity and smooth alternatives need the calibration that is forbidden in this pass.
- **O6.** The real broker commission is unconfirmed.
- **O7.** Whether a loss-bound-only construction exists for the average-of-conditional-means target is unestablished.

### 5.3 What was not done in this document

No code, no simulation, no synthetic calibration, no DEV, VALID or HOLD access, no change to protocol v1.2, PR #4, PR #5, V2.2 or V2.2.1, no adoption of X^M or any statistical method, and none of the six decisions was taken. Results from the literature (Hoeffding, Lehmann and Romano, Howard and Ramdas, Waudby-Smith and Ramdas, Wang and Ramdas) are recalled, not re-verified.
