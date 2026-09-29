# The Rollover Clock: Debt Maturity, the Central-Bank Balance Sheet, and the Debt Limit of a Reserve-Currency Sovereign

*Preliminary working paper, September 2026. Comments welcome. Replication code and data: <https://github.com/dingningpei/rollover-clock> (Appendix C).*

## Abstract

When can a sovereign that borrows in its own reserve currency keep rolling its debt over, and what stops it if it cannot? We separate two layers of the answer.

The first is a **fiscal layer**. Debt is locally stable if and only if the primary surplus offsets at least a share φ* = 1 − g/(r + ψb) of the marginal interest cost of debt. We show that this threshold does not depend on the maturity structure of the debt, for any repricing kernel.

The second is an **inflation layer**. If the fiscal response falls short, surprise inflation must substitute for it. How much inflation that takes depends on how fast the consolidated interest-bearing liabilities of the Treasury and the central bank reprice, which we call the *rollover clock*, and on how much of the consolidated balance sheet inflation can erode: nominal debt that has not yet repriced, and currency.

We measure the clock security by security for the United States from 1980 to 2025, both for the Treasury alone and consolidated with the Federal Reserve, with reserves treated as overnight debt. The clock predicts the official average interest rate on marketable debt far better than maturity summaries do. Over 12–36 months the mean absolute error is 0.05–0.07 percentage points, against 0.28–0.62 for a WAM-based clock. Frozen at end-2021, it tracks the 2022–25 rise in Treasury interest costs within about 0.05 pp. Using the Fed's actual policy rates and expenses, it also reproduces the Fed's cumulative operating loss: a predicted deferred asset of −$245bn against −$243bn actual at end-2025.

Three findings follow:

1. The fiscal threshold in 2023–25 (φ* ≈ 0.47) is not unusual. It is back in its 1980–2007 range after the 2008–21 period in which r + ψb < g.
2. What has changed is the fiscal response. The legislated offset of higher interest costs fell from about 0.39 before 2004 to about zero since.
3. Quantitative easing raised the inflation needed per unit of relief by roughly 60%. Before 2008 the Fed financed its Treasuries with currency, which inflation erodes; QE financed them with interest-bearing reserves that reprice overnight.

Together, these make the inflation needed to cover today's fiscal gap after a permanent 1pp rate rise the largest since at least 1980: about 1.0–1.1 pp per year for a decade, almost twice the pre-2008 peak. The U.S. is far from a default limit. Its binding constraint is the cost of the inflation tax.

---

## 1. Introduction

Can an issuer that replaces maturing high-coupon debt with new low-coupon debt keep doing so forever? For a sovereign that issues the world's reserve currency and whose central bank can buy its bonds, default is a choice rather than a constraint. The question is then not whether a debt limit exists but what form it takes.

This paper argues that the limit has two layers, and that they depend on the debt's maturity in opposite ways.

**The fiscal layer is maturity-free.** In a transparent model of consolidated debt dynamics, where the market rate rises with debt and the average rate on outstanding debt reprices toward it at a speed set by maturity, debt is locally stable if and only if

$$(1-\phi)\,(r+\psi b)<g .$$

Here φ is the share of marginal interest cost offset by the primary surplus, and r + ψb is the marginal interest cost of debt. With φ = 0 this is the condition of Mian, Straub and Sufi (2025). We show that the repricing speed cancels from it, and that the result holds for any maturity structure. Shorter debt makes a rate shock bite faster, but it does not change whether the system is stable.

**The inflation layer depends on maturity and on what the government owes.** If the fiscal response is below the threshold, the gap must be closed some other way. For a reserve-currency sovereign that other way is inflation. Sustained surprise inflation erodes only nominal liabilities that have not yet repriced: debt that rolls over at new, Fisher-adjusted rates escapes, and currency, which never reprices, does not. The inflation needed to replace a missing fiscal offset therefore depends on the rollover clock P(h), the share of a permanent rate shock that has reached the average rate after h years, and on the erodible share E(h) of the balance sheet:

$$\Delta\pi^{req}(H)=(\phi^*-\hat\phi)^+\,\Delta r\,\frac{\int_0^H P(h)\,dh}{\int_0^H E(h)\,dh}.$$

Two implications follow. First, inflation on debt only buys time. Debt reprices, so its erosion runs out as the horizon lengthens; only currency can be taxed permanently. At end-2025, covering the fiscal gap with a permanent inflation tax on currency would take about 5.6 pp of extra inflation a year, before any flight from cash. Second, the relevant balance sheet is the **consolidated** one. A central bank that holds Treasuries against currency turns interest-bearing debt into a zero-interest liability that inflation erodes. One that holds them against interest-bearing reserves does the opposite: it shortens the maturity of the government's liabilities to the private sector and takes them out of the inflation-tax base. The inflation substitute becomes costlier, even though Treasury-only maturity statistics may be lengthening at the same time.

**Measurement.** We build the clock from the Monthly Statement of the Public Debt (MSPD) security by security for 2001–2025, net the Fed's holdings CUSIP by CUSIP from SOMA data, add reserves and reverse repos as overnight liabilities, and add currency to the base that inflation erodes. We extend the series to 1980 with hand-transcribed maturity distributions of privately held debt from the Treasury Bulletin. The security-level reconstruction matches official totals exactly in every year. The Fed's holdings match its balance sheet exactly from 2007.

**Validation.** Two tests show that the clock is a sufficient statistic for interest-cost pass-through in a way that maturity summaries are not.

- *Historical backtest.* Across 22 year-end origins from 2001 to 2024, projecting the average interest rate on marketable debt from the portfolio known at the origin and realized yields gives a mean absolute error of 0.047 pp at 12 months (0.091 pp with trend rather than realized borrowing). A clock based only on weighted-average maturity gives 0.279 pp.
- *Out-of-sample test on 2022–25.* Freezing the balance sheets at end-2021, the clock tracks the 1.9 pp rise in the Treasury's average rate over four years within about 0.05 pp. The WAM-based clock captures less than a fifth of the first year's rise. On the Fed side, overnight repricing of reserves against the frozen end-2021 asset book reproduces the Fed's cumulative loss: a predicted deferred asset of −$245bn against −$243bn actual.

**Findings.** Putting the two layers on a common 1980–2025 timeline gives three results.

1. The fiscal threshold today is ordinary. φ* in 2023–25 is about 0.47, within its 1980–2007 range of roughly 0.1–0.56. The 2008–21 period, when the threshold was negative, was the exception.
2. The fiscal response is not ordinary. Before 2004 the legislated offset of higher interest costs was about 0.39, roughly enough to meet the threshold; the 1990 and 1993 budget agreements belong to that regime. Since 2004 it has been about zero (Auerbach and Yagan 2024).
3. QE removed the Fed's inflation-tax cushion. Before 2008, consolidating with the Fed roughly halved the inflation needed per unit of relief, because the Fed's Treasuries were financed by currency. Since 2009 the consolidated and Treasury-only requirements have been about equal, and the consolidated ratio has risen from 1.2–1.6 to 2.0–2.6.

The combined metric, the inflation needed to cover the fiscal gap after a +1pp permanent rate rise, is therefore at its highest in the sample in 2023–25: 1.01–1.12 pp per year for ten years, against 0.61 in 2007 and 0.23 in 1981.

Counterfactuals rank the levers. Restoring the pre-2004 fiscal response cuts the required inflation by about 84%. Undoing QE, so that the Fed holds only as many Treasuries as it has currency outstanding, cuts it by about 18%. Returning reserves to their 2019 level or terming out a tenth of bills cuts it by 6–7%. Losing 50–100bp of convenience yield raises it by 8–14%.

**Contribution.** None of the ingredients is new on its own:

- debt dynamics with endogenous rates (Mian, Straub and Sufi 2025; Lorenzoni and Werning 2019);
- consolidated Treasury–Fed maturity (Greenwood, Hanson, Rudolph and Summers 2014; TBAC 2020, 2026; OBR 2021);
- maturity and the inflation tax (Cochrane 2001, 2022; Hilscher, Raviv and Reis 2022; Barro and Bianchi 2026);
- fiscal responses to debt service (Bohn 1998; Auerbach and Yagan 2024; Eichengreen, Menuet and Donnat 2026).

The paper's contribution is to put them together:

1. A proof that the fiscal threshold is maturity-free, alongside a closed-form inflation requirement in which maturity enters only through the measured clock.
2. A long time series (1980–2025) of the full consolidated repricing profile for the U.S. It generalizes the scalar reset measures used in debt management, and is validated out of sample; we found no earlier series of this kind.
3. A two-layer, year-by-year distance to the limit that separates what fiscal policy must do from what balance-sheet policy changes. It quantifies the effect of consolidation on the inflation requirement, which Barro and Bianchi (2026) note would be desirable but for which "data are not available."

Section 2 reviews related work. Section 3 presents the model. Section 4 builds and validates the clock. Section 5 presents the two-layer limit from 1980 to 2025, and Section 6 the counterfactuals. Section 7 concludes.

## 2. Related literature

**Debt limits with endogenous rates.**
- Mian, Straub and Sufi (2025) derive fiscal space when R − G rises with debt. Their free-lunch condition, R < G − ϕ with ϕ the sensitivity of R − G to log debt (ψb in our notation), is the φ = 0 case of ours. Their maturity extension works through the convenience yield of long versus short debt in steady state, not through repricing speed.
- Lorenzoni and Werning (2019) show that responsive fiscal rules and longer maturity can rule out slow-moving debt crises. Their mechanism runs through default equilibria.
- Li and Merkel (2026) show that QE can shift a default boundary inward by depleting central-bank capital. Their §4.8 notes that in transition longer maturity reduces rollover pressure, since only a fraction 1/n of the stock comes due each period, while in steady state it shrinks the fiscal dividend from convenience yields.
- Our setting has no default. Maturity leaves the stability threshold unchanged and instead governs the inflation alternative. In the tradition of Sargent and Wallace (1981) and Davig, Leeper and Walker (2011), the non-default limit is where fiscal adjustment stops and inflation must take over; we make that boundary measurable.
- Related work on sustainability and debt capacity includes Blanchard (2019), Mehrotra and Sergeyev (2021), Reis (2021), Ghosh et al. (2013), and the convenience-yield literature (Krishnamurthy and Vissing-Jorgensen 2012; Choi, Kirpalani and Perez 2026; Jiang et al. 2024).

**Consolidated maturity and QE.**
- Greenwood et al. (2014) measure consolidated Treasury–Fed duration and show that Treasury's maturity extension offset about a third of QE's reduction in privately held duration (35% from a 2007 baseline; 63% from December 2008).
- The Treasury Borrowing Advisory Committee (2020) computed consolidated Treasury–Fed maturity and duration. Since 2022, Treasury's refunding materials report a consolidated weighted-average next rate reset (WANRR), which TBAC (2026) reviews; it treats the part of SOMA that funds reserves, ON RRP and other interest-bearing Fed liabilities as repricing overnight.
- The OBR documents the same shortening for the UK.
- CBO (2022), Levin, Lu and Nelson (2022), Cavallo et al. (2019) and d'Avernas et al. (2024) discuss the fiscal risk this creates.
- We generalize the scalar reset measures to the full repricing profile, build it from 1980, and validate it on realized outcomes, including the Fed's 2022–25 losses.

**Maturity and the inflation tax.**
- In the fiscal theory of the price level, maturity determines whether fiscal news shows up as inflation now or later (Cochrane 2001, 2022, 2023).
- Barro and Bianchi (2026) scale fiscal spending shocks by debt times duration in explaining 2020–23 inflation.
- Hilscher, Raviv and Reis (2022) and Aizenman and Marion (2011) show that short U.S. maturity limits how far inflation can erode debt.
- Reis (2017) argues that QE, by bringing more debt due, lowers the price increase a fiscal crisis requires.
- Section 3.4 reconciles these signs. A one-time level jump is maturity-neutral, a transitory surprise favors short debt, and sustained inflation favors long debt.
- We invert the erosion calculation into a required inflation rate as a function of the measured clock, and quantify how consolidation shifts it.

**Fiscal responses.**
- Bohn (1998, 2008) estimates a positive U.S. response of surpluses to debt.
- Eichengreen, Menuet and Donnat (2026) find that surpluses respond to debt service more than to debt stocks, and more strongly when r > g. Their object is a log-log elasticity, and they describe their evidence as descriptive.
- Auerbach and Yagan (2024) find that legislated U.S. fiscal feedback, including the response to lagged net interest, was substantial before 2004 and has been about zero since.
- We use these estimates as the historical benchmark φ̂. The paper does not depend on estimating φ ourselves; φ enters only through a threshold comparison.

## 3. Model

### 3.1 Setup

All variables are ratios to GDP. The government is consolidated: Treasury plus central bank. b is net debt to the private sector (marketable Treasuries held outside the central bank, plus reserves and reverse repos), r̄ is the average effective rate on b, r the market rate on new issuance, s the primary surplus, and g growth.

$$\dot b=(\bar r-g)\,b-s,\qquad r=r^*+\psi\,(b-b^*),\qquad s=s^*+\phi\,(\bar r b-r^*b^*).$$

**Repricing.** If debt matures at rate λ and grows through net issuance at rate Ḃ/B, the average rate obeys, exactly,

$$\dot{\bar r}=\big(\lambda+\dot B/B\big)(r-\bar r).$$

We verify this against a cohort-level simulation (maximum error 4×10⁻⁷). Near a steady state the repricing speed is Λ = λ + g: new debt issued to keep pace with growth is priced at the new rate. For a general maturity structure with repricing distribution F(h), the share of a permanent rate shock that reaches the average rate after h years is

$$P(h)=1-\big(1-F(h)\big)e^{-gh}.$$

We call P(h) the *rollover clock*.

### 3.2 The fiscal layer is maturity-free

Linearizing around the steady state gives

$$\det J=\Lambda\,[\,g-(1-\phi)(r^*+\psi b^*)\,],$$

and the steady state is stable if and only if (1 − φ)(r* + ψb*) < g. Λ cancels.

The result holds for any repricing kernel. The characteristic equation is x = a + cψK(x), with a = (1 − φ)r* − g, c = (1 − φ)b*, and K the Laplace transform of the kernel. Since |K(x)| ≤ 1 for Re x ≥ 0, and the condition implies |a| > |cψ|, no root lies in the closed right half-plane.

When fiscal adjustment instead responds with a lag, a numerical scan over 3,180 parameter combinations with λ ∈ [0.05, 5] found no case in which λ changes stability. Maturity also barely moves the asymptotic divergence rate when the system is unstable.

The minimum stabilizing offset is

$$\phi^*=1-\frac{g}{r+\psi b}.$$

### 3.3 The inflation layer

Let a permanent real-rate rise Δr add extra interest Δr·b·P(h), where P is the clock of all interest-bearing liabilities; inflation-indexed debt reprices its real coupon at maturity like any other bond.

Sustained surprise inflation Δπ lowers the real value of nominal liabilities that have not yet repriced. Two parts of the consolidated balance sheet qualify:
- non-indexed debt N, with its own clock P_N;
- currency C, which pays no interest and never reprices. Before October 2008 this also includes reserves.

Inflation-indexed debt cannot be eroded. Per unit of interest-bearing debt b, the erodible share at horizon h is

$$E(h)=\frac{N}{b}\,\big[1-P_N(h)\big]+\frac{C}{b}.$$

Replacing an unfinanced share u of the extra interest over horizon H requires

$$\Delta\pi^{req}(H)=u\,\Delta r\,\frac{\int_0^H P}{\int_0^H E} .$$

If all debt were nominal and there were no currency, the denominator would be ∫(1 − P).

**Corollary (inflation on debt only buys time).** ∫₀^∞[1 − P_N] = ∫₀^∞[1 − F_N]e^{−gh} dh is finite, so the debt part of the erosion base runs out. Only the currency part grows with H. As H → ∞,

$$\Delta\pi^{req}(H)\to u\,\Delta r\,\frac{b}{C},$$

the permanent inflation tax on currency that covers the gap. Without currency, Δπ^req(H) → ∞. At end-2025 b/C ≈ 12, so with u = 0.46 the limit is about 5.6 pp per year indefinitely, before any fall in currency demand. In 2007 it was about 1.9.

**Combined metric.** Local stability requires offsetting the share φ* of marginal interest cost. With a historical offset φ̂ < φ*, the missing share is u = (φ* − φ̂)⁺. This gives the two-layer distance to the limit:

$$\Delta\pi^{gap}(H)=(\phi^*-\hat\phi)^+\,\Delta r\,\frac{\int_0^H P}{\int_0^H E}.$$

The approximations are:
- φ* is evaluated at r rather than r + Δr, which is conservative;
- flows are matched undiscounted;
- Δr is exogenous;
- currency demand does not respond to inflation, which makes the requirement a lower bound;
- H is finite.

### 3.4 Which inflation? Reconciling the maturity sign

Let w(s) be the share of payments due at s and p(s) the cumulative surprise in the price level. Real erosion is b∫w(s)p(s)ds. How maturity matters depends on how persistent the price-level path is:

| Price-level path | Erosion | Effect of shorter maturity |
|---|---|---|
| Permanent one-time jump, p(s) = Δp | b·Δp | none |
| Transitory surprise until τ | b·Δp·F(τ) | helps (Reis 2017: "more of the debt coming due") |
| Sustained inflation, p(s) = Δπ·s | b·Δπ·D | hurts (Cochrane; Barro–Bianchi; HRR; this paper) |

QE therefore makes a front-loaded surprise more effective and a persistent inflation tax less effective. Because our question is whether inflation can stand in for a missing fiscal response over a horizon, we use the sustained object. We also report the one-time level jump, Δp^req = u·Δr·∫₀^H P / (N/b + C/b), which depends on maturity only through the cost of the shock.

## 4. Measuring the rollover clock

### 4.1 Data

**Treasury, 2001–2025.** MSPD Table 3 (marketable), year-end snapshots, one row per CUSIP.
- Repricing dates are maturity for bills, notes, bonds and TIPS, and one week for FRNs.
- The security-level sums match the official unmatured totals for all 25 year-ends, to within 2×10⁻¹⁴ %. One MSPD label is misspelled ("Tresasury Floating Rate Notes", 2016); we handle it.

**Federal Reserve, 2003–2025.**
- SOMA Treasury holdings by CUSIP, including TIPS inflation compensation, from the New York Fed. They match H.4.1 Treasuries held outright exactly from 2007, and within 0.25–0.51% in 2003–06.
- Reserve balances and reverse repurchase agreements from H.4.1. Both reprice overnight.
- Currency pays no interest, so it is not part of interest-bearing debt b. It enters the erosion base of the inflation layer (Section 3.3), measured as H.4.1 currency in circulation in the same week as reserves. Reserves paid no interest before October 2008, so through 2007 they are counted with currency.
- The Treasury General Account is intragovernmental and excluded.

**1980–2002.** Treasury Bulletin table FD-5 (FD-7 before 1983): marketable debt held by private investors, which excludes the Fed and government accounts, by remaining-maturity bucket.
- Reserves paid no interest before October 2008, so privately held marketable debt is the consolidated interest-bearing liability for that period.
- We transcribed 24 December rows from FRASER scans. Every row's buckets sum to its total within ±1 (in $mn).
- Checks against the exact data:
  - The December 2003 FD-5 total (2,908,029) matches MSPD minus SOMA (2,910,053) within 0.07%.
  - Bucketing understates the 10-year inflation-layer ratio by a stable 0.077 (s.d. 0.016) on 2003–07 exact data. We correct for this.
- FD-5 does not separate inflation-indexed notes (first issued in 1997). We remove them from the erosion base by maturity bucket, using the Treasury Bulletin's FD-2 totals and the maturities of the TIPS issues outstanding at each year-end. Before 2003 this also removes the Fed's small TIPS holdings (8% of TIPS in 2003).
- The zero-interest base is currency in circulation plus reserve balances, December averages (FRED CURRCIR and RESBALNS). It was 27–33% of privately held marketable debt in 1980–2002, against 8% in 2025.

**Precedent.** Security-level accounting of U.S. debt returns and its effect on debt/GDP dynamics goes back to Hall and Sargent (2011); we use the same MSPD-based building blocks to measure repricing speed rather than realized returns.

**Other inputs.** Yields are H.15 constant-maturity series; the −9999 missing-value code (20-year CMT, 1987–93) is treated as missing. Official average interest rates on marketable debt and the auction record are from FiscalData. GDP is from BEA.

### 4.2 The clock, 1980–2025

Figure 1 shows P(1), the share of a permanent rate shock that reaches the average rate within a year.

![Figure 1](figures/fig1_rollover_clock.png)

*Figure 1. Rollover clock P(1). Orange: consolidated. For 1980–2002 this is privately held debt from FD-5 buckets (open markers); for 2003–2025 it is MSPD net of SOMA plus reserves and RRP. Blue: Treasury only (MSPD, 2001–).*

Four features stand out.

1. The clock slowed steadily through the 1980s as Treasury lengthened maturity: P(1) fell from 0.51 in 1980 to about 0.37 by 1987.
2. Before 2008 the consolidated clock was slightly *slower* than the Treasury-only clock, because the Fed held mostly bills.
3. QE reversed this. In 2021 the consolidated P(1) was 0.53 against 0.33 for the Treasury alone, and consolidated WAM was 4.1 years against 6.0. Treasury was lengthening while the Fed was shortening.
4. QT narrowed the gap, but in 2025 the consolidated P(1) was still about 9 points higher.

### 4.3 Validation I: historical backtest

From each year-end origin t (2001–2024; 2004 is omitted because the official figure is missing), we project the official average interest rate on marketable debt for 36 months:
- surviving securities keep their rate;
- maturing principal and net new borrowing are reissued at realized H.15 yields, using the auction mix of year t.

We score the change in the rate against two benchmarks: a scalar clock based on weighted-average maturity (WAM), which is the information in maturity summaries, and no change.

**Table 1. Backtest: mean absolute error (bias) of the predicted change in the average rate, pp**

| Horizon | Clock, realized borrowing | Clock, trend borrowing | WAM-only clock | No change | Origins |
|---|---|---|---|---|---|
| 12 months | 0.047 (−0.003) | 0.091 (+0.068) | 0.279 (−0.108) | 0.389 (+0.118) | 22 |
| 24 months | 0.066 (−0.005) | 0.155 (+0.116) | 0.502 (−0.254) | 0.693 (+0.167) | 21 |
| 36 months | 0.071 (−0.019) | 0.170 (+0.140) | 0.620 (−0.431) | 0.815 (+0.146) | 20 |

The full repricing profile cuts the error of a maturity summary by a factor of three to nine.

The largest ex-ante misses come from unanticipated bill-financed deficits: 2007 (+0.52 pp at 12 months) and 2019 (+0.32 pp). They shrink to +0.14 and +0.08 pp once realized borrowing is used.

### 4.4 Validation II: the 2022–25 tightening from end-2021

We freeze both balance sheets at end-2021, before the first rate increase, and feed in realized rates and quantities.

**Treasury (Figure 2A).**
- The clock predicts a 0.94 pp rise in the average rate by December 2022 (actual 0.89) and 1.96 pp by December 2025 (actual 1.93).
- The WAM-only clock predicts 0.17 and 1.57.

**Federal Reserve (Figure 2B).** The model is as follows.
- The asset book is frozen at end-2021:
  - Treasuries at their coupons;
  - MBS at the end-2021 book coupon of 2.48%;
  - TIPS inflation compensation as realized;
  - premium amortization net of discount accretion.
- Reserves reprice overnight at the IORB rate and reverse repos at the ON RRP rate. Both come from the FOMC target range: IORB is the top of the range minus 10bp; ON RRP is the bottom plus 5bp, and the bottom itself from 19 December 2024.
- Other expenses (operating expenses plus dividends minus other income) are taken year by year from the Reserve Banks' combined financial statements.

The model reproduces the Fed's deferred asset at each year-end:

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Predicted | −18 | −142 | −226 | −245 |
| Actual | −18 | −132 | −215 | −243 |

($bn.) Premium amortization matters: without it, the model understates losses by about 40%.

Component check against the combined financial statements:
- Modeled reverse-repo interest expense matches the statements within about 1% in every year ($40.8bn vs $42.0bn in 2022; $103.3bn vs $104.3bn in 2023), which validates the policy-rate rule.
- Modeled interest on reserves is 6–10% below the statements' "depository institutions and others" line, which also covers other deposits.
- Modeled interest income on the frozen book is $6–23bn below actual.

The close deferred-asset fit therefore partly reflects offsetting errors on the income and expense sides. The out-of-sample claim rests mainly on the timing and size of the expense leg.

![Figure 2](figures/fig2_2022_test.png)

*Figure 2. Out-of-sample test from end-2021. A: change in the official average rate on marketable debt; the clock (dashed) against the WAM-only clock (dotted). B: Fed deferred asset; frozen end-2021 asset book with reserves repricing overnight.*

The consolidated clock is thus validated where QE matters most. The 2022–25 rate shock reached consolidated interest costs through a Treasury clock that passed through about 0.9 pp within a year, and through an overnight Fed clock that passed through at once and appeared in the budget as lost remittances.

## 5. The two-layer limit, 1980–2025

### 5.1 Parameters

- **ψ = 3bp per pp of debt/GDP**, range 2–4.5. Sources: Laubach 2009 (3–4); Engen and Hubbard 2005 (≈ 3); Plante, Richter and Zubairy 2025 (3.0–3.5); Bhatt et al. 2026 (3–4); Bi, Phillot and Zubairy 2026 (2.8 at peak, from identified supply shocks). CBO's 2bp (Neveu and Schafer 2024) is the low case.
- **φ̂ = 0.39 through 2003 and ≈ 0 from 2004.** These are Auerbach and Yagan's (2024) estimates of the legislated response to lagged net interest (0.386, s.e. 0.131, for 1984–2003; −0.31, s.e. 0.41, for 2004–24; their Table 3). The pre-2004 coefficient comes from semi-annual data and falls to about −0.12 once their projected-surplus control is added. For the upper end of the sensitivity range we also use de Groot, Holm-Hadulla and Leiner-Killinger (2015), whose European estimates imply an offset of about 0.7 over ten years. We use a Bohn-based 0.25 as a sensitivity.
- **r** is the steady-state marginal cost of the existing structure: each security's original tenor priced at current yields. Before 2003 we use remaining-maturity pricing, corrected by its measured 0.28 pp gap on 2003–2025.
- **g**, expected nominal growth, is proxied by realized forward ten-year nominal GDP growth through 2015. From 2016 we use the December FOMC Summary of Economic Projections: the longer-run median real GDP growth (1.8–1.9%) plus the 2% inflation objective. Trailing ten-year growth is a sensitivity. In 2013–15, when both measures exist, the SEP-based g (4.0–4.3%) was below realized forward growth (5.2–5.4%), which was inflated by 2021–22.

### 5.2 Results

![Figure 3](figures/fig3_limit_map.png)

*Figure 3. Two-layer limit. Top: fiscal threshold φ* (line; band spans g and ψ) and historical offset φ̂ (dashed). Middle: inflation-layer ratio ∫P/∫E, consolidated (erosion base includes currency, and reserves before 2008) and for the Treasury's own marketable debt. Bottom: inflation needed to cover the gap (φ* − φ̂)⁺ after a +1pp permanent rate rise, pp per year for 10 years.*

**Table 2. Two-layer limit by period (consolidated; g forward; ψ = 3bp)**

| Period | φ* | φ̂ | Gap | Inflation-layer ratio | Inflation to cover gap (pp/yr) |
|---|---|---|---|---|---|
| 1981–85 | 0.41–0.56 | 0.39 | 0.02–0.17 | 1.4–1.6 | 0.04–0.23 |
| 1986–99 | 0.12–0.43 | 0.39 | ≈ 0 | 1.3–1.6 | ≈ 0 |
| 2005–07 | 0.28–0.44 | 0 | 0.28–0.44 | 1.4–1.5 | 0.38–0.61 |
| 2009–21 | mostly < 0 (2017–19: 0.11–0.21) | 0 | ≈ 0 (2017–19: 0.11–0.21) | 2.0–2.6 | ≈ 0 (2017–19: 0.23–0.43) |
| 2023–25 | 0.46–0.48 | 0 | 0.46–0.48 | 2.2–2.4 | 1.01–1.12 |

Three readings follow.

1. **The fiscal threshold is ordinary today.** The period that stands out is 2008–21, when r + ψb < g and debt stabilized with no fiscal response. That period is over.
2. **The fiscal response is not ordinary.**
   - Before 2004, a legislated offset of about 0.39 roughly met the threshold, and the high-rate 1980s and early 1990s ended in consolidation.
   - Since 2004 the offset has been about zero, so the gap equals the threshold itself.
   - The gap first opened in 2005–07, when φ* was 0.28–0.44; the 2008–21 low-rate period then hid it.
3. **QE raised the price of the inflation substitute.** The consolidated ratio rose from 1.2–1.6 in 1980–2007 to 2.0–2.6 from 2008 on.
   - Before QE, consolidation roughly halved the ratio relative to the Treasury's own liabilities (0.49–0.53 times the Treasury-only value in 2003–07). The Fed held Treasuries against currency, which inflation erodes.
   - Since 2009 the two have been about equal (0.86–1.19). The Fed's additional Treasuries and MBS are financed by interest-bearing reserves that reprice overnight.

The combined requirement in 2023–25 is the largest since 1980, about 1.8 times its 2006–07 level.

The equivalent one-time surprise rise in the price level is about 3.3% (3.27–3.42% in 2023–25). As Section 3.4 predicts, it is much less sensitive to consolidation: since 2009 the consolidated value has been 0.95–1.05 times the Treasury-only value.

**Sensitivity.**
- *Horizon.* With H = 5 the 2023–25 requirement is 0.60–0.69 pp per year; with H = 15 it is 1.33–1.46.
- *Erosion base.* If all debt counted as erodible and currency were ignored, the requirement would be 1.22–1.41. Ignoring currency alone raises the 2025 consolidated ratio by a third (2.92 against 2.18).

### 5.3 Can φ be identified from U.S. data?

We tried to estimate φ directly with the clock.
- **Instrument.** The predicted interest-cost change b_t·P_t(1)·Δr_{t+1} uses the predetermined repricing exposure.
- **Outcome.** The subsequent change in the NIPA primary surplus, excluding Fed remittances.
- **Controls.** The rate change, debt, growth and the lagged surplus.

In annual data for 1980–2024 the instrument is weak:
- First-stage F ≈ 6.7, falling below 1 once Δr·b is controlled.
- The implied φ is implausible (6–26).

The reason is that the U.S. repricing speed varies too little over time. P(1) has a standard deviation of 0.056, and the instrument is 99% correlated with Δr·b.

We therefore do not use an own estimate. The paper's conclusions rest on the threshold comparison with literature values of φ̂ (Section 5.1 and Table 3). Maturity structures and QE intensities differ widely across countries, so a cross-country panel is the natural way to identify φ with this design.

## 6. Counterfactuals

**Table 3. End-2025 counterfactuals** (+1pp permanent rate rise, H = 10; baseline φ̂ = 0)

| Scenario | φ* | Gap | Inflation to cover gap (pp/yr) | Change vs. baseline | One-time jump (%) |
|---|---|---|---|---|---|
| Baseline (consolidated; g = 3.8%, SEP) | 0.46 | 0.46 | 1.00 | — | 3.26 |
| Fiscal response restored (φ̂ = 0.39) | 0.46 | 0.07 | 0.16 | −84% | 0.51 |
| Fiscal response 0.25 (Bohn-based) | 0.46 | 0.21 | 0.46 | −54% | 1.50 |
| No QE: Fed Treasuries = currency, no reserves | 0.46 | 0.46 | 0.83 | −18% | 3.07 |
| Treasury's own liabilities (Fed ignored) | 0.46 | 0.46 | 1.02 | +1% | 3.31 |
| QT: reserves to $1.9tn, Treasuries back to private | 0.46 | 0.46 | 0.94 | −6% | 3.20 |
| Treasury terms out: 10% of bills → 10y | 0.46 | 0.46 | 0.93 | −7% | 3.18 |
| Convenience yield −50bp | 0.50 | 0.50 | 1.08 | +8% | 3.51 |
| Convenience yield −100bp | 0.53 | 0.53 | 1.15 | +14% | 3.73 |
| Trend growth 4% | 0.43 | 0.43 | 0.95 | −5% | 3.07 |
| Trend growth 3.5% | 0.50 | 0.50 | 1.08 | +8% | 3.55 |
| ψ = 2bp (CBO) | 0.38 | 0.38 | 0.82 | −18% | 2.67 |
| ψ = 4.5bp | 0.55 | 0.55 | 1.20 | +20% | 3.90 |

In the No-QE scenario the Fed holds only as many Treasuries as it has currency outstanding, as before 2008. The rest return to private holders pro rata to the SOMA maturity structure, and reserves and reverse repos go to zero. Debt/GDP is held at its baseline, to isolate the change in composition.

- **The fiscal response is the dominant lever.**
- **Balance-sheet policy moves only the inflation layer.** QE, QT and Treasury's maturity choice change the cost of the inflation substitute by 6–18%, but they cannot change the threshold.
- **Losing the convenience yield, slower growth and a steeper debt-rate schedule raise the threshold itself.**

Two limitations: the balance-sheet scenarios hold r fixed and ignore the term-premium effects of QE and QT, and all scenarios are static comparisons.

## 7. Conclusion

A reserve-currency sovereign does not run into a debt wall. It runs into a choice between fiscal adjustment and an inflation tax.

The size of the required adjustment, the fiscal layer, depends on r − g, on how sensitive rates are to debt, and on the debt level, and not on maturity. How expensive the inflation alternative is, the inflation layer, depends on how fast the consolidated liabilities reprice and on how much of them inflation can erode. Both are measurable. QE made the clock faster and, by replacing the Fed's currency funding with interest-bearing reserves, shrank the base the inflation tax falls on.

The United States in 2023–25 faces an ordinary fiscal threshold with an unusually absent fiscal response and an unusually fast consolidated clock. As a result, inflation would buy less time per point than at any point since 1980. Inflation on debt only buys time, and a permanent inflation tax on currency alone would take about 5.6 pp a year. The durable resolutions are a return of the fiscal response that met the threshold before 2004, or a one-time surprise revaluation of the debt.

**Open issues.**
- The fiscal response φ̂ comes from the literature, and its post-2004 collapse rests mainly on one study. Our own exposure × rate-shock design is too weak in U.S. annual data (Section 5.3); a cross-country panel is the natural next step.
- Expected growth after 2015 comes from the FOMC's longer-run projections, not from a model of trend growth.
- The balance-sheet counterfactuals abstract from term-premium effects.
- The combined metric is a first-order, undiscounted composition.
- Currency demand is held fixed. A sustained inflation tax would shrink it, so the requirements are lower bounds in that respect.

---

## References

- Aizenman, J. and N. Marion (2011). "Using Inflation to Erode the US Public Debt." *Journal of Macroeconomics* 33(4): 524–541.
- Auerbach, A. J. and D. Yagan (2024). "Robust Fiscal Stabilization." *Brookings Papers on Economic Activity* 2024(2): 239–322; NBER WP 33374.
- Barro, R. J. and F. Bianchi (2026). "Fiscal Influences on Inflation in OECD Countries, 2020–2023." *Economic Journal* 136(674): 626–654; NBER WP 31838.
- Bhatt, A., A. M. Diercks, B. Eyal and A. Skaperdas (2026). "The Causal Effect of Debt on Interest Rates." Finance and Economics Discussion Series 2026-031, Board of Governors of the Federal Reserve System.
- Bi, H., M. Phillot and S. Zubairy (2026). "Treasury Supply Shocks: Propagation Through Debt Expansion and Maturity Adjustment." NBER WP 35098.
- Blanchard, O. (2019). "Public Debt and Low Interest Rates." *American Economic Review* 109(4): 1197–1229.
- Bohn, H. (1998). "The Behavior of U.S. Public Debt and Deficits." *Quarterly Journal of Economics* 113(3): 949–963.
- Bohn, H. (2008). "The Sustainability of Fiscal Policy in the United States." In R. Neck and J.-E. Sturm (eds.), *Sustainability of Public Debt*, 15–49. MIT Press.
- Cavallo, M., M. Del Negro, W. S. Frame, J. Grasing, B. A. Malin and C. Rosa (2019). "Fiscal Implications of the Federal Reserve's Balance Sheet Normalization." *International Journal of Central Banking* 15(5): 255–306.
- Congressional Budget Office (2022). "How the Federal Reserve's Quantitative Easing Affects the Federal Budget." September. Publication 58457.
- Choi, J., R. Kirpalani and D. J. Perez (2026). "US Public Debt and Safe Asset Market Power." *Journal of Political Economy* 134(5): 1506–1560. doi:10.1086/739824. Earlier version: "The Macroeconomic Implications of US Market Power in Safe Assets," NBER WP 30720 (2022).
- Cochrane, J. H. (2001). "Long-Term Debt and Optimal Policy in the Fiscal Theory of the Price Level." *Econometrica* 69(1): 69–116.
- Cochrane, J. H. (2022). "Inflation Past, Present and Future: Fiscal Shocks, Fed Response, and Fiscal Limits." NBER WP 30096.
- Cochrane, J. H. (2023). *The Fiscal Theory of the Price Level.* Princeton University Press.
- d'Avernas, A., A. Hubert de Fraisse, L. Ning and Q. Vandeweyer (2024). "The Fiscal Cost of Quantitative Easing." SSRN 5009335.
- Davig, T., E. M. Leeper and T. B. Walker (2011). "Inflation and the Fiscal Limit." *European Economic Review* 55(1): 31–47.
- de Groot, O., F. Holm-Hadulla and N. Leiner-Killinger (2015). "Cost of Borrowing Shocks and Fiscal Adjustment." *Journal of International Money and Finance* 59: 23–48.
- Eichengreen, B., M. Menuet and G. Donnat (2026). "From Stocks to Flows: Debt Service and Fiscal Sustainability." NBER WP 35459.
- Engen, E. M. and R. G. Hubbard (2005). "Federal Government Debt and Interest Rates." In M. Gertler and K. Rogoff (eds.), *NBER Macroeconomics Annual 2004*, Vol. 19. MIT Press.
- Ghosh, A. R., J. I. Kim, E. G. Mendoza, J. D. Ostry and M. S. Qureshi (2013). "Fiscal Fatigue, Fiscal Space and Debt Sustainability in Advanced Economies." *Economic Journal* 123(566): F4–F30.
- Greenwood, R., S. G. Hanson, J. S. Rudolph and L. H. Summers (2014). "Government Debt Management at the Zero Lower Bound." Hutchins Center on Fiscal and Monetary Policy at Brookings, Working Paper 5.
- Hall, G. J. and T. J. Sargent (2011). "Interest Rate Risk and Other Determinants of Post-WWII U.S. Government Debt/GDP Dynamics." *AEJ: Macroeconomics* 3(3): 192–214.
- Hilscher, J., A. Raviv and R. Reis (2022). "Inflating Away the Public Debt? An Empirical Assessment." *Review of Financial Studies* 35(3): 1553–1595.
- Jiang, Z., H. Lustig, S. Van Nieuwerburgh and M. Z. Xiaolan (2024). "The U.S. Public Debt Valuation Puzzle." *Econometrica* 92(4): 1309–1347.
- Krishnamurthy, A. and A. Vissing-Jorgensen (2012). "The Aggregate Demand for Treasury Debt." *Journal of Political Economy* 120(2): 233–267.
- Laubach, T. (2009). "New Evidence on the Interest Rate Effects of Budget Deficits and Debt." *Journal of the European Economic Association* 7(4): 858–885.
- Levin, A. T., B. L. Lu and W. R. Nelson (2022). "Quantifying the Costs and Benefits of Quantitative Easing." NBER WP 30749.
- Li, W. and S. Merkel (2026). "Quantitative Easing and Government Debt Sustainability." NBER WP 35421; SSRN 5743942.
- Lorenzoni, G. and I. Werning (2019). "Slow Moving Debt Crises." *American Economic Review* 109(9): 3229–3263.
- Mehrotra, N. R. and D. Sergeyev (2021). "Debt Sustainability in a Low Interest Rate World." *Journal of Monetary Economics* 124(Supplement): S1–S18.
- Mian, A., L. Straub and A. Sufi (2025). "A Goldilocks Theory of Fiscal Deficits." *American Economic Review* 115(12): 4253–4291; NBER WP 29707.
- Neveu, A. R. and J. Schafer (2024). "Revisiting the Relationship Between Debt and Long-Term Interest Rates." CBO Working Paper 2024-05.
- Office for Budget Responsibility (2021). "Debt Maturity, Quantitative Easing and Interest Rate Sensitivity." Box in *Economic and Fiscal Outlook – March 2021*.
- Plante, M., A. W. Richter and S. Zubairy (2025). "Revisiting the Interest Rate Effects of Federal Debt." NBER WP 34018.
- Reis, R. (2017). "QE in the Future: The Central Bank's Balance Sheet in a Fiscal Crisis." *IMF Economic Review* 65(1): 71–112; NBER WP 22415.
- Reis, R. (2021). "The Constraint on Public Debt When r < g but g < m." BIS WP 939.
- Sargent, T. J. and N. Wallace (1981). "Some Unpleasant Monetarist Arithmetic." *Federal Reserve Bank of Minneapolis Quarterly Review* 5(3): 1–17.
- Treasury Borrowing Advisory Committee (2020). Charge presentation on the Federal Reserve balance sheet and the consolidated government balance sheet. February 2020 Quarterly Refunding, U.S. Treasury.
- Treasury Borrowing Advisory Committee (2026). "Bill Purchases and the Consolidated Balance Sheet." Charge presentation, 3 February 2026, U.S. Treasury.

---

## Appendix A. Data construction details

**Repricing distribution.** For each year-end t and each liability i with par (or balance) wᵢ and years to repricing τᵢ, the repricing distribution is F_t(h) = Σᵢ wᵢ·1{τᵢ ≤ h} / Σᵢ wᵢ. Repricing dates are:
- maturity for bills, notes, bonds and TIPS;
- one week for floating-rate notes (weekly reset);
- zero (overnight) for reserve balances and reverse repurchase agreements.

The clock adds growth-financing issuance at the new rate: P_t(h) = 1 − (1 − F_t(h))e^{−gh}, with g = 4% for the descriptive clock (Figure 1) and the year's g in the limit calculations. The erosion clock P_N is built the same way from non-indexed liabilities only.

**Zero-interest base.** Currency in circulation from H.4.1 (series RESTBC), in the same week as reserves, from 2003. Before that, December averages of currency in circulation and reserve balances (FRED CURRCIR and RESBALNS). The two currency sources differ by about 1% where they overlap. Reserves are in the zero-interest base through 2007 and in overnight interest-bearing debt from 2008.

**Treasury-only stock.** All unmatured marketable Treasuries in MSPD Table 3 at the year-end, one row per CUSIP, including those held by the Federal Reserve.

**Consolidated stock.** Marketable Treasuries minus SOMA holdings, matched by CUSIP (with TIPS inflation compensation), plus reserve balances and reverse repos from the H.4.1 week closest to, and not after, the year-end. SOMA CUSIPs that are absent from the MSPD year-end snapshot all mature between the SOMA date and 31 December (at most $61bn, 0.3% of the stock) and are dropped.

**1980–2002.** FD-5 reports privately held marketable debt in five remaining-maturity buckets: within 1 year, 1–5, 5–10, 10–20 and 20 years and over. Within each bucket we spread par uniformly over the bucket (upper edge of the last bucket: 30 years). On the exact security-level data for 2003–07, this bucketing understates the ten-year inflation-layer ratio ∫P/∫E by 0.077 (s.d. 0.016), ∫P by 0.167, and the remaining-maturity rate r by 0.28 pp. We add these corrections to the 1980–2002 values. TIPS (1997–2002) are removed from the erosion base by bucket: their December totals come from Treasury Bulletin table FD-2 and their maturity profile from the TIPS issues outstanding at each year-end.

**Required inflation.** The integrals in Result 3 are evaluated by the trapezoid rule on a grid with a step of one month over [0, 15] years. F(h) is interpolated between the sorted repricing dates of the security-level data.

**Backtest projection (Section 4.3).**
- From the year-end portfolio, every surviving security keeps its rate: the coupon for notes and bonds, the real coupon for TIPS, and the 3-month rate plus spread for FRNs.
- Each month, maturing principal plus net new borrowing is reissued in year t's gross auction mix, at that month's H.15 yield for the tenor.
- The projected average rate is the par-weighted rate of the resulting portfolio. We score its change against the change in FiscalData's official average interest rate on total marketable debt.
- "Realized borrowing" interpolates the actual path of marketable debt. "Trend borrowing" grows the year-t stock at 4% a year.

**Fiscal-reaction coefficient.** Auerbach and Yagan (2024) estimate the legislated primary-surplus response to lagged net interest. Their coefficient is in dollars of surplus per dollar of interest, which is the marginal offset φ of Section 3. Eichengreen, Menuet and Donnat (2026) instead estimate a log-log elasticity of the surplus to debt service. That elasticity maps to φ only through s/(r̄b), which is undefined when the primary balance is negative, so we use it as qualitative evidence only.

## Appendix B. Proofs

**B.1 Repricing law.** Let B be the face value of debt and R = r̄B total interest. Debt matures at rate λ; the average rate on the maturing flow is r̄ (exact under exponential maturity). Maturing debt and net issuance Ḃ are refinanced at the market rate r, so Ṙ = (λB + Ḃ)r − λB·r̄. Then

$$\dot{\bar r}=\frac{\dot R}{B}-\bar r\frac{\dot B}{B}=\Big(\lambda+\frac{\dot B}{B}\Big)(r-\bar r).$$

A cohort-level simulation reproduces this law to within 4×10⁻⁷, which is the time-step error.

**B.2 Stability with exponential repricing.** Take the state (b, r̄) and let Λ = λ + g. Around the steady state (b*, r*),

$$J=\begin{pmatrix}(1-\phi)r^*-g & (1-\phi)b^*\\ \psi\Lambda & -\Lambda\end{pmatrix},\qquad \det J=\Lambda\,[\,g-(1-\phi)(r^*+\psi b^*)\,].$$

Write a = (1 − φ)r* − g and c = (1 − φ)b* ≥ 0 for φ ≤ 1. Then det J > 0 if and only if a + cψ < 0. That implies a < 0, and therefore tr J = a − Λ < 0. So the steady state is locally stable if and only if (1 − φ)(r* + ψb*) < g, whatever Λ is.

**B.3 Any repricing kernel.** Let the average rate be a weighted history of market rates, r̄(t) = ∫₀^∞ k(s) r(t − s) ds, with k ≥ 0 and ∫k = 1. The cumulative kernel ∫₀^h k is the rollover clock P(h). Linearizing gives ḃ = a·b + c·r̄ with r = ψb, so modes e^{xt} solve

$$x=a+c\psi K(x),\qquad K(x)=\int_0^\infty k(s)e^{-xs}\,ds .$$

- If Re x ≥ 0, then |K(x)| ≤ 1, so Re x = a + cψ Re K(x) ≤ a + cψ. Under the stability condition, a + cψ < 0. This is a contradiction, so every root has Re x < 0.
- Conversely, if a + cψ > 0, the real function f(x) = a + cψK(x) − x is positive at x = 0 and tends to −∞. It therefore has a positive real root.

Stability thus depends on (a, c, ψ) and not on the kernel. The exponential kernel k(s) = Λe^{−Λs} gives K(x) = Λ/(Λ + x) and reproduces B.2.

With lagged fiscal adjustment, ṡ = κ[s* + φ(r̄b − r*b*) − s], the determinant condition is the same. A scan of 3,180 combinations of (r, φ, κ) with λ ∈ [0.05, 5] finds no case in which λ changes stability.

**B.4 Required inflation (Result 3).** A permanent real-rate rise Δr raises interest by Δr·b·P(h) at horizon h, where P is the clock of all interest-bearing debt b = N + I (nominal plus indexed).

A sustained surprise inflation Δπ lowers the real value of a nominal liability until it reprices, since repriced debt carries a Fisher-adjusted coupon. Indexed debt I is not eroded at all. Currency C pays no interest and never reprices, so it is eroded at every h. The erosion flow at h is therefore Δπ·{N[1 − P_N(h)] + C} = Δπ·b·E(h). Setting cumulative erosion over [0, H] equal to the unfinanced share u of cumulative extra interest,

$$\Delta\pi\,b\int_0^H E=u\,\Delta r\,b\int_0^H P\;\Rightarrow\;\Delta\pi^{req}(H)=u\,\Delta r\,\frac{\int_0^H P}{\int_0^H E} .$$

With u = (φ* − φ̂)⁺ this is the combined metric of Section 3.3.

Three remarks:
1. φ* is evaluated at r rather than r + Δr. Since φ* rises with r, the metric is conservative, and the error is second order in Δr.
2. Since ∫₀^∞(1 − P_N) = ∫₀^∞(1 − F_N)e^{−gh}dh < ∞, both ∫₀^H P and ∫₀^H E grow like H, with slopes 1 and C/b. The required rate therefore converges to u·Δr·b/C as H → ∞. Without currency it diverges.
3. For a one-time level jump Δp, erosion is (N + C)·Δp regardless of maturity. So Δp^req = u·Δr·∫₀^H P / (N/b + C/b).

## Appendix C. Reproduction

The replication package is at <https://github.com/dingningpei/rollover-clock>. It contains the code (`src/`) and three hand-collected inputs (`data/manual/`):
- the Treasury Bulletin FD-5/FD-7 December rows for 1980–2003, transcribed from FRASER scans;
- the Federal Reserve Banks' combined income statements for 2022–2025;
- the FOMC's December longer-run growth projections.

Everything else is downloaded from public sources: the Treasury (FiscalData: MSPD, auctions, average interest rates), the Federal Reserve Board (H.4.1 and H.15 bulk files), the New York Fed (SOMA holdings, EFFR) and the BEA (NIPA). The command

```
bash reproduce.sh
```

downloads the inputs, runs the model checks and the full pipeline, and writes all tables to `data/processed/` and Figures 1–3 to `paper/figures/`.
