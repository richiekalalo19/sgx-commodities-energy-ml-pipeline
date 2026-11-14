"""Figure A1: Kalman commodity sensitivity for the nine daily-mapped core counters, against the rolling
one-year Dimson regression. Shaded: the lockbox period (from 1 May 2025), not used to estimate the model.

Reads reports/tables/kalman_paths_all.csv and rolling_dimson_all.csv (written by scripts/15_residuals_all.py).
Run:  .venv/bin/python scripts/fig_kalman_all.py
Output: reports/figures/figA1_kalman_all.png
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

root = Path(__file__).resolve().parents[1]
T = root / "reports" / "tables"
kal = pd.read_csv(T / "kalman_paths_all.csv", index_col=0, parse_dates=True)
roll = pd.read_csv(T / "rolling_dimson_all.csv", index_col=0, parse_dates=True)
LOCKBOX = pd.Timestamp("2025-05-01")

names = {"5TP": "CNMC Goldmine (gold)", "5GI": "Interra Resources (Brent)", "5WH": "Rex International (Brent)",
         "T13": "RH PetroGas (Brent)", "DU4": "Mermaid Maritime (Brent)", "RE4": "Geo Energy (coal)",
         "5E2": "Seatrium (Brent)", "5LY": "Marco Polo Marine (Brent)", "G92": "China Aviation Oil (jet fuel)"}
order = kal.ffill().iloc[-1].sort_values(ascending=False).index

fig, axes = plt.subplots(3, 3, figsize=(10, 7.5), sharex=True)
for ax, code in zip(axes.flat, order):
    k = kal[code].dropna()
    if code == "RE4":                    # API2 coal series ends 26 Dec 2025; later values are not informed by coal
        k = k[:"2025-12-26"]
    ax.axvspan(LOCKBOX, kal.index[-1], color="gainsboro", alpha=0.6, zorder=0)
    ax.axhline(0, color="black", linewidth=0.6)
    if code in roll:
        r = roll[code].dropna()
        ax.plot(r.index, r.values, color="grey", linewidth=0.8, alpha=0.8)
    ax.plot(k.index, k.values, color="tab:blue", linewidth=1.5)
    ax.set_title(names[code], fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(linestyle=":", alpha=0.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

handles = [plt.Line2D([], [], color="tab:blue", linewidth=1.5, label="Kalman filter (smoothed)"),
           plt.Line2D([], [], color="grey", linewidth=0.8, label="Rolling 1-year regression"),
           plt.Rectangle((0, 0), 1, 1, color="gainsboro", alpha=0.6, label="Lockbox (not used in estimation)")]
fig.legend(handles=handles, loc="upper center", ncol=3, fontsize=9, frameon=False)
fig.supylabel("Sensitivity (% counter move per 1% commodity move)", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = root / "reports" / "figures" / "figA1_kalman_all.png"
fig.savefig(out, dpi=200)
print("saved", out)
