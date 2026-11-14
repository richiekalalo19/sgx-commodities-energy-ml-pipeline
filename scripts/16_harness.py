"""Builds the validation harness (plan task 7) from the residual series and checks it. No model is fit.

Checks
  1. Leakage: every training window ends at least EMBARGO sessions before its test period, and no
     development target window touches the lockbox.
  2. Universe (D2): eligible counters per month.
  3. Random predictions: the share of seeds with |t| > 1.96 for mean IC should be close to 5%.
  4. Oracle predictions (prediction = target): IC of 1 and a positive tercile spread.
  Both also report ROC-AUC per date (auc_up: residual > 0; auc_top: realised top tercile): about 0.5
  for random predictions, 1 for the oracle.

Outputs: data/processed/harness/{dev.parquet, lockbox_sealed.parquet, seal.json, folds.json}
         reports/tables/harness_folds.csv, harness_universe.csv, harness_selftest.csv
Run:  .venv/bin/python -I scripts/16_harness.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from fyp import config, harness
from fyp.panel import load

warnings.filterwarnings("ignore")

resid = pd.read_parquet(config.PROCESSED / "residuals_daily.parquet")
sessions = resid.index
close, volume = load("equity_close"), load("equity_volume")
elig = harness.eligibility(close[resid.columns], volume[resid.columns], sessions)
samples = harness.build_samples(resid, elig)
fold_table = [f for h in harness.HORIZONS for f in harness.folds(sessions, h)]
seal = harness.save(samples, fold_table)

# 1. Leakage
pos = pd.Series(np.arange(len(sessions)), index=sessions)
lb = sessions.searchsorted(harness.LOCKBOX_START)
problems = 0
dev = samples[samples["part"] == "dev"]
for f in fold_table:
    h = f["horizon"]
    train = dev[(dev["horizon"] == h) & (dev["date"] <= pd.Timestamp(f["train_last"]))]
    if len(train):
        window_end = pos[train["date"].max()] + h
        if not window_end + harness.EMBARGO < sessions.searchsorted(pd.Timestamp(f["test_start"])):
            problems += 1
if (pos[dev["date"]].values + dev["horizon"].values >= lb).any():
    problems += 1
print(f"Leakage check: {'passed' if problems == 0 else f'{problems} problems'}")

# 2. Universe per month (20-session samples)
m = samples[(samples["horizon"] == 20)]
uni = m.groupby("date").agg(counters=("code", "count"), eligible=("eligible", "sum")).reset_index()
uni.to_csv(config.TABLES / "harness_universe.csv", index=False)
latest = m[m["date"] == m["date"].max()]
print(f"Eligible counters per month: min {uni['eligible'].min()}, median {uni['eligible'].median():.0f}, "
      f"max {uni['eligible'].max()}; latest ({latest['date'].iloc[0].date()}): {int(latest['eligible'].sum())} of "
      f"{len(latest)}; ineligible now: {', '.join(latest.loc[~latest['eligible'], 'code']) or 'none'}")

# 3 and 4. Random and oracle predictions on the development test folds
test = dev[dev["fold"] != "train-only"].copy()
rows = []
for h in harness.HORIZONS:
    th = test[test["horizon"] == h]
    tstats, r_auc_up, r_auc_top = [], [], []
    for seed in range(100):
        th = th.assign(pred=np.random.default_rng(seed).standard_normal(len(th)))
        s = harness.per_date_scores(th)
        tstats.append(s["ic"].mean() / (s["ic"].std(ddof=1) / np.sqrt(len(s))))
        r_auc_up.append(s["auc_up"].mean())
        r_auc_top.append(s["auc_top"].mean())
    tstats = np.array(tstats)
    oracle = harness.per_date_scores(th.assign(pred=th["target"]))
    mean_ic, lo, hi = harness.stationary_bootstrap(oracle["tercile_spread"], mean_block=6 if h == 20 else 12, n_boot=500)
    rows.append(dict(horizon=h, test_dates=len(oracle), median_names=float(oracle["n"].median()),
                     random_false_positive_rate=float((np.abs(tstats) > 1.96).mean()),
                     random_mean_t=float(tstats.mean()),
                     random_auc_up=float(np.mean(r_auc_up)), random_auc_top=float(np.mean(r_auc_top)),
                     random_auc_top_p95=float(np.quantile(r_auc_top, 0.95)),
                     oracle_auc_up=float(oracle["auc_up"].mean()), oracle_auc_top=float(oracle["auc_top"].mean()),
                     oracle_ic=float(oracle["ic"].mean()),
                     oracle_tercile_spread=mean_ic, oracle_spread_ci_low=lo, oracle_spread_ci_high=hi))
self_test = pd.DataFrame(rows)
self_test.to_csv(config.TABLES / "harness_selftest.csv", index=False)
pd.DataFrame(fold_table).to_csv(config.TABLES / "harness_folds.csv", index=False)

counts = samples.groupby(["horizon", "part"]).size().unstack()
pd.set_option("display.width", 220)
print("\nSamples by horizon and part\n", counts.to_string())
print("\nFolds\n", pd.DataFrame(fold_table).to_string(index=False))
print("\nSelf-test (development test folds only)\n", self_test.round(4).to_string(index=False))
print(f"\nLockbox sealed: {seal['rows']} rows from {seal['lockbox_start']}, sha256 {seal['sha256'][:12]}...")
