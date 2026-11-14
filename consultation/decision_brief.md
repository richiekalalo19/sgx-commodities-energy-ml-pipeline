# Consultation brief · A1088-261

Meeting with A/P Wong Jia Yiing, Patricia · Thursday 22 October 2026, 4.30pm on Zoom (or Friday if moved)
Prepared 21 October 2026 · Plan v2: https://claude.ai/artifact/5RhYSMRFbPKMAhjD8SjEwG

How to use this: section 1 is the opening two minutes. Section 3 holds eight decisions, each with a
recommendation; tick or change them before the meeting. Section 4 is the list of questions to ask.
Figures are in `reports/figures` (light and dark versions); the slide draft is `consultation/deck_draft.pptx`.

---

## 1. Opening: where the project stands

Since the proposal of 14 September:

- I read the 2026 final-year project in this group (Wijaya, 2026) and adopted its model-comparison design as a
  new Aim 4.
- I wrote plan v2, which makes ten changes and keeps the proposal's title and aims.
- I built the data pipeline and pulled 13 years of daily data for 28 equities (the SGX universe, plus Indonesian
  and Malaysian growers for the levy test) and 23 commodity, currency and index series.
- I ran the first checks. Three results bear on direction:
  1. **Timing.** Between two fifths and three quarters of a commodity move reaches SGX counters in the next
     session, so same-day regressions understate pass-through by about half.
  2. **The export-ban natural experiment works.** In the first session after Indonesia announced its 2022 export
     ban, Indonesian growers on SGX lost 7.1% against their market while Malaysian growers gained 3.9%. The gap of
     11.1 points has a t-statistic of −5.9.
  3. **The commodity is a minority of the return.** It adds 0.4 to 19 percentage points of explained weekly
     variance per counter, but it changes measured alpha at portfolio level.

## 2. Evidence

All numbers are preliminary: free data, no Bloomberg yet. File names refer to `reports/`.

| # | Finding | Key numbers | Figure or table |
|---|---|---|---|
| 1 | Liquidity filter | 15 of 17 trading core counters clear S$100k median daily value; 12 clear S$1M. Interra Resources has not traded since 31 Jan 2025. Golden Energy and Resources (delisted 2023) is missing from free data. | `liquidity_dots`, `turnover_filter.csv` |
| 2 | Trading costs | Round trip 0.36% (Keppel) to 2.08% (Golden Agri, Rex), including fees of 0.13% a side with GST. Closes are unchanged on 30 to 38% of days for the penny counters. | `liquidity_costs.csv`, `equity_quality.csv` |
| 3 | Timing | Next-day share of the response 39 to 76% for the counters with a reliable daily underlying (Brent, gold, coal, jet fuel); lag t-statistics up to 10; Dimson sensitivity about twice the same-day estimate. Holds with Brent spot instead of futures. | `passthrough_dumbbell`, `passthrough_daily.csv`, `passthrough_brent_spot_check.csv` |
| 4 | Drift | Kalman sensitivity of CNMC to gold rose from 0.44 to 1.60; Rex to Brent ranges 0.30 to 0.76. | `kalman_5TP`, `kalman_5WH` |
| 5 | Size of the commodity component | Weekly R-squared added: CNMC 19 points, Rex 9, RH PetroGas 8.5, First Resources 6.7, Bumitama 5.7, Golden Agri 2.2, Wilmar 0.7, Marco Polo 0.4 (palm figures provisional, see 8). Sector basket: 0.49 to 0.65. | `passthrough_weekly_r2.csv`, `plumbing_jensen_alpha.csv` |
| 6 | Asymmetry | No significant up-down difference except Geo Energy, where rises transmit more (p = 0.001). On synthetic data a 30% asymmetry was detected in 1 of 5 runs, so this test has little power. | `passthrough_asymmetry_weekly.csv`, `synthetic_recovery.csv` |
| 7 | Export-levy experiment | Ban announcement: gap −11.1 points (t = −5.9). Lifting announcement: +4.4 (t = 2.3). Routine levy changes (July 2022 suspension, May 2025 rise): no measurable effect. 3 of 5 high-confidence events have the expected sign. | `levy_ban_2022`, `levy_event_cars.csv` |
| 8 | Palm data problem | The free daily palm series (CPO=F) is a monthly-average swap: first-of-month moves 3.9 times normal, late-month moves 0.27 times early-month. Unusable for daily work. | `data_quality_notes.md` |
| 9 | Method validation | Kalman with the next-day term: error 0.10; without it: 0.40, missing about 42% of the response. Monte Carlo power of the IC test matches the plan's table; false positives 4 to 5.5%. | `synthetic_recovery`, `synthetic_ic_power.csv` |
| 10 | Power | An 18-month lockbox detects only IC ≥ 0.16. Eight to ten years of walk-forward data detect 0.06 to 0.07; weekly, about 0.03. | `power_curve` |
| 11 | Plumbing run | Naive equal-weight sector basket: 7.5% a year net, Sharpe 0.34, drawdown −54%. STI total return: 8.4%, Sharpe 0.65. Alpha −0.9% a year (STI only) and −1.6% (with commodities), neither significant. | `plumbing_basket`, `plumbing_summary.csv` |
| 12 | Fundamentals and announcements | Free fundamentals cover FY2021 to FY2025 only. The SGX announcements API is closed. | `fundamentals_coverage.csv` |

## 3. Decisions to formalise

### D1. Where the daily commodity prices come from

- **Options.** (a) Bloomberg at the Business Library: daily Bursa FCPO, Newcastle coal, freight, Golden Energy's
  history and fundamentals. (b) Free monthly series for palm and coal (IMF via FRED), daily for Brent and gold.
  (c) The free daily palm series, CPO=F.
- **Recommendation.** (a), with (b) as the fallback. Never (c) for daily work.
- **Why.** Finding 8. Plan v2 sets the decision point at 31 October. The shopping list is
  `data/reference/bloomberg_shopping_list.csv`.
- **Ask.** Any advice on terminal access, or exports from earlier students in the group.

### D2. Universe and liquidity filter

- **Options.** Median daily traded value over the trailing 12 months of at least S$100k (15 counters today),
  S$500k (14) or S$1M (12).
- **Recommendation.** S$100k, applied point-in-time each month. Mermaid Maritime and Union Gas fall below it
  today; Interra is inactive. Keep Golden Energy and Resources until its delisting, using Bloomberg prices.
- **Why.** Finding 1. Higher thresholds remove few names but cost power: with 12 counters the detectable IC over
  eight years rises from 0.07 to 0.09.

### D3. Horizons and rebalancing

- **Options.** Daily (as in the 2026 study), weekly, monthly.
- **Recommendation.** Models predict 5- and 20-day residual returns; the strategy rebalances monthly; daily data is
  used only for estimation.
- **Why.** Findings 2 and 10. The plumbing run's 4% monthly turnover costs 0.7% a year; a strategy turning over half
  its book monthly in these counters would pay 5 to 9% a year.

### D4. Size of the machine-learning stage

- **Options.** Four models, as in Wijaya (2026): ridge, XGBoost, LSTM and Temporal Fusion Transformer. Or two:
  ridge and XGBoost.
- **Recommendation.** Four, with the TFT as the first item dropped if time runs short.
- **Why.** It mirrors the prior work she supervised and adds a linear floor. The environment already works on this
  laptop (LSTM test passes; XGBoost computes SHAP values).
- **Ask.** Whether she wants the deep models, given about eighteen counters.

### D5. Fundamentals: the ranking and its data

- **Options.** A ranking only; the pass-through explanation only; both.
- **Recommendation.** Both: a sector-relative F-score ranking each reporting period (her stage 01), plus the panel
  test of what explains pass-through. Hand collection limited to the five plantation counters.
- **Why.** The brief asks for "criteria and ranking methodology". Finding 12: the 2014 to 2020 statements must
  come from Bloomberg or annual reports.
- **Ask.** Whether the sector-relative version is acceptable as the stage 01 method.

### D6. How Aim 1 is framed

- **Options.** Keep the proposal's claim that a large share of each counter's return is the commodity, or revise it.
- **Recommendation.** Revise to: commodity sensitivities are significant, drift over time and arrive partly in the
  next session, but they explain a minority of weekly variance, and removing them changes measured alpha.
- **Why.** Findings 3, 4, 5 and 11. It is also good news for the project: most of the return is left for the FA, NA
  and TA layers to explain.

### D7. News design

- **Recommendation.** Event studies on residuals with severity tiers, and the export-levy experiment as the
  headline test. Results-announcement timestamps come from Bloomberg or Factiva, since the SGX API is closed.
- **Why.** Findings 7 and 12. Large, surprising policy shocks move the residual; routine levy changes do not, which
  is itself a severity result.

### D8. Validation

- **Recommendation.** The walk-forward record with bootstrap intervals is the primary evidence; the lockbox is a sign
  check; every null is stated against its detectable effect; the asymmetry tests are flagged as low-power.
- **Why.** Findings 6, 9 and 10.

## 4. Questions for Prof. Wong

1. Which title was registered on Stafflink before 5 October: the proposal's "An FA–NA–TA Trading Framework for SGX
   Energy and Commodity Equities", or an alternative?
2. The interim report: its date, length and format, and what the video must cover.
3. Is a sector-relative F-score ranking acceptable as the stage 01 method?
4. Four models, as in Wijaya (2026), or ridge and XGBoost only?
5. May Wijaya (2026) be cited as prior work in this group?
6. Does EEE require a declaration on the use of generative AI tools in the reports?
7. Any advice on Bloomberg terminal access, or data from previous students?

## 5. Next three weeks, to the interim report

- **This week (S1 W10).** Bloomberg session using the shopping list; a Factiva test export; the commodity data
  decision by 31 October.
- **S1 W11.** Rerun Aim 1 with FCPO; freeze the harness and seal the lockbox; write up the synthetic validation.
- **S1 W12 to W13.** Interim report chapters 1 to 4, and the video.

## 6. What is already set up

`~/Desktop/FYP/fyp-pipeline` holds the code, data and results. `./run_all.sh` rebuilds everything in about five
minutes. Two Python environments: `.venv` for data and statistics, `.venv-ml` for the model stack (PyTorch 2.2.2,
pytorch-forecasting, XGBoost, scikit-learn, optuna, shap). The README describes every module.

## 7. Caveats

- Free data only. Daily palm results use CPO=F and are flagged as unreliable.
- Some event dates in `data/reference/levy_events.csv` are marked "verify"; only the high-confidence events enter
  the sign count.
- Sharpe ratios and alphas use a zero risk-free rate until a SORA or T-bill series is added.
- The cost table prices each counter at its latest close; the plumbing run uses the price at each rebalance.
