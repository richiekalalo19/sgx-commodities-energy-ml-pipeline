"""Figure 5: CNMC Goldmine's sensitivity to gold, Kalman smoother against a rolling one-year window.

Reads the Kalman path saved by scripts/11_passthrough_timing.py (reports/tables/kalman_5TP.csv) and
recomputes the rolling one-year Dimson estimate with the same inputs as script 11.
Run:  .venv/bin/python scripts/fig_kalman_cnmc.py
Output: reports/figures/fig05_kalman_cnmc.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from fyp.betas import equity_on_calendar, on_calendar, rolling_dimson
from fyp.panel import load

root = Path(__file__).resolve().parents[1]
START = "2014-01-01"

close = load("equity_adjclose")
daily = load("series_daily")
sgx = daily["sti"].dropna().index
sgx = sgx[sgx >= START]
r = equity_on_calendar(close["5TP"], sgx)
gold = on_calendar(daily["gold"], sgx)
sti = on_calendar(daily["sti"], sgx)
roll = rolling_dimson(r, gold, sti)

kal = pd.read_csv(root / "reports" / "tables" / "kalman_5TP.csv", index_col=0, parse_dates=True)["beta_total_smoothed"]

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(roll.index, roll.values, color="grey", linewidth=1, alpha=0.8, label="Rolling 1-year regression")
ax.plot(kal.index, kal.values, color="tab:blue", linewidth=2, label="Kalman filter (smoothed)")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel("Sensitivity to gold")
ax.set_xlabel("Year")
ax.grid(linestyle=":", alpha=0.6)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=9, frameon=False)

fig.tight_layout()
out = root / "reports" / "figures" / "fig05_kalman_cnmc.png"
fig.savefig(out, dpi=200)
print("saved", out)
print(f"Kalman: start {kal.iloc[0]:.2f}, end {kal.iloc[-1]:.2f}, max {kal.max():.2f}")
print(f"Rolling: min {roll.min():.2f}, max {roll.max():.2f}")
