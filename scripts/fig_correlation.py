"""Figure: correlation of weekly counter returns with the market and commodity series.

Weekly (Friday) log returns, Jan 2014 to Apr 2025 (before the lockbox). Weekly rather than daily
because commodity markets close after SGX and many counters do not trade every day. Palm is left
out because the free palm series (CPO=F) is a monthly-average swap.

Run:  .venv/bin/python scripts/fig_correlation.py
Output: reports/figures/fig_correlation.png, reports/tables/correlation_weekly.csv
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fyp import config

START, END = "2014-01-01", "2025-04-30"
series = {"sti_etf": "STI", "brent": "Brent", "gold": "Gold", "coal": "Coal (API2)", "jet": "Jet fuel",
          "henry_hub": "US gas", "dry_bulk": "Dry bulk", "usdsgd": "USD/SGD"}

core = [c for c in config.UNIVERSE if c.group == "core"]
px = pd.read_parquet(config.PROCESSED / "equity_adjclose.parquet")[[c.code for c in core]]
mk = pd.read_parquet(config.PROCESSED / "series_daily.parquet")[list(series)]


def weekly(df):
    return np.log(df.loc[START:END].resample("W-FRI").last()).diff()


r = weekly(px)
m = weekly(mk).rename(columns=series)
corr = pd.DataFrame({col: r.corrwith(m[col], min_periods=52) for col in m.columns})
corr.index = [f"{c.name} ({c.code})" for c in core]
root = Path(__file__).resolve().parents[1]
corr.round(3).to_csv(root / "reports" / "tables" / "correlation_weekly.csv")

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
ax.set_xticks(range(corr.shape[1]))
ax.set_xticklabels(corr.columns, rotation=45, ha="right")
ax.set_yticks(range(corr.shape[0]))
ax.set_yticklabels(corr.index, fontsize=8.5)
for i in range(corr.shape[0]):
    for j in range(corr.shape[1]):
        v = corr.iat[i, j]
        if np.isfinite(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 0.4 else "black")
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
fig.tight_layout()
fig.savefig(root / "reports" / "figures" / "fig_correlation.png", dpi=200)

obs_daily = int(pd.read_parquet(config.PROCESSED / "equity_close.parquet").notna().sum().sum())
print(corr.round(2).to_string())
print("equity price observations (all 28 counters, full history):", obs_daily)
print("weekly returns used:", int(r.notna().sum().sum()))
