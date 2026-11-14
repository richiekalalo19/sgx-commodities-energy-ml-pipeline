# A1088-261 pipeline

Code and data for the FYP *An FA–NA–TA Trading Framework for SGX Energy and Commodity Equities*
(plan v2: https://claude.ai/artifact/5RhYSMRFbPKMAhjD8SjEwG).

## Quick start

```bash
cd ~/fyp-pipeline
./run_all.sh              # download fresh data and rebuild every table and figure (about 5 minutes)
./run_all.sh --offline    # rebuild from the latest downloads without the network
```

Results land in `reports/tables` (CSV) and `reports/figures` (PNG and SVG, light and dark). Each script also
runs on its own, for example `.venv/bin/python -I scripts/13_levy_event_study.py`.

## Layout

| Path | What it holds |
|---|---|
| `src/fyp/config.py` | Universe (28 counters), market series, SGX tick schedule, fee assumptions. Edit here, once. |
| `src/fyp/data_sources.py` | Yahoo Finance, FRED and SGX downloaders. Raw files are written to dated folders and never edited. |
| `src/fyp/panel.py` | Processed panel: wide daily tables per field, on each exchange's own calendar. |
| `src/fyp/betas.py` | Same-day, Dimson lead-and-lag, asymmetric and rolling pass-through regressions (HAC errors). |
| `src/fyp/kalman.py` | Time-varying coefficients by Kalman filter and smoother, noise variances by maximum likelihood. |
| `src/fyp/costs.py` | Tick size, fees, round-trip cost, Corwin–Schultz spread, Amihud illiquidity. |
| `src/fyp/events.py` | Market-model event studies with portfolio aggregation for clustered events. |
| `src/fyp/synthetic.py` | Synthetic counters with planted answers, and the IC-test power simulation. |
| `src/fyp/power.py` | Minimum detectable information coefficient. |
| `src/fyp/plotting.py` | Shared chart style (validated palette, light and dark). |
| `scripts/01`–`04` | Collection: market data, processed panel, fundamentals coverage probe, point-in-time fundamentals panel (FY2022–FY2025, usable 60 days after fiscal year end). |
| `scripts/10`–`16` | Analyses: liquidity and costs, pass-through timing, synthetic validation, export-levy event study, plumbing run, Kalman residual series with rolling benchmark and diagnostics for all core counters, and the validation harness. |
| `src/fyp/harness.py` | Validation harness, fixed 10 Nov 2026: D2 universe (trailing-year median traded value ≥ S$100k), D3 targets (5- and 20-session forward residual returns), walk-forward folds 2018 to Apr 2025 with purge and a 20-session embargo, lockbox from 1 May 2025 opened once with `open_lockbox("open once")`, and the IC, tercile-spread and hit-rate scores. |
| `data/reference/` | Universe, series list, collection log, levy event dates with sources, Bloomberg shopping list. |
| `reports/data_quality_notes.md` | What the first collection run found wrong with the free data, and what to do about it. |
| `consultation/` | Brief and slide draft for the October consultation. |
| `interim/` | `FYP_Interim_Progress.pptx`: the plan as a table, then work done so far (built by `tools/deck/build_progress_deck.js`). |

## Environments

- `.venv` (Python 3.13): data, statistics and figures. Everything in `scripts/` runs here.
- `.venv-ml` (Python 3.12): the Aim 4 model stack: torch 2.2.2, lightning, pytorch-forecasting, XGBoost, scikit-learn,
  optuna, shap. Torch 2.2.2 is the last release built for Intel Macs, which is why this environment uses Python 3.12.
  XGBoost needs the OpenMP runtime, installed with `brew install libomp` (remove with `brew uninstall libomp`).

## Known gaps

See `reports/data_quality_notes.md`. In short: the free daily palm-oil series (`CPO=F`) is a monthly-average swap
and cannot stand in for Bursa FCPO; Golden Energy and Resources (delisted 2023) is missing; free fundamentals cover
FY2021 onward only; the SGX announcements API is closed; there is no free Singapore risk-free rate on FRED.
`data/reference/bloomberg_shopping_list.csv` lists what to pull from the Business Library terminal.
