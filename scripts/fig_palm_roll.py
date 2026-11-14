"""Why the free daily palm series (CPO=F) is unusable: its moves cluster on the first trading day of
each month (contract roll) and fade late in the month (the month's average is mostly fixed).
Brent and gold futures are shown for comparison.

Sample: all available days from 2013. Ratios of mean absolute daily log returns.
Run:  .venv/bin/python scripts/fig_palm_roll.py
Output: reports/tables/palm_roll_check.csv, reports/figures/fig_palm_roll.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
d = pd.read_parquet(root / "data" / "processed" / "series_daily.parquet")

rows = []
for col, label in [("palm", "Palm oil (CPO=F)"), ("brent", "Brent"), ("gold", "Gold")]:
    r = np.log(d[col].dropna()).diff().dropna().abs()
    month = pd.Series(r.index.to_period("M"), index=r.index)
    pos = month.groupby(month).cumcount()                  # 0 = first trading day of the month
    rev = month.groupby(month).cumcount(ascending=False)   # 0 = last trading day of the month
    rows.append(dict(series=label, days=len(r),
                     first_day_vs_other=r[pos == 0].mean() / r[pos > 0].mean(),
                     last5_vs_first5=r[rev < 5].mean() / r[pos < 5].mean()))
tab = pd.DataFrame(rows)
tab.round(2).to_csv(root / "reports" / "tables" / "palm_roll_check.csv", index=False)
print(tab.round(2).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
colours = ["tab:orange", "tab:blue", "tab:olive"]
for ax, col, ylabel in [(axes[0], "first_day_vs_other", "First trading day / other days"),
                        (axes[1], "last5_vs_first5", "Last five days / first five days")]:
    ax.bar(tab["series"], tab[col], color=colours)
    ax.axhline(1, color="black", linewidth=0.8, linestyle="--")
    ax.set_ylabel(ylabel)
    for i, v in enumerate(tab[col]):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(tab[col].max() * 1.2, 1.3))
    ax.tick_params(axis="x", labelsize=8.5)
fig.tight_layout()
fig.savefig(root / "reports" / "figures" / "fig_palm_roll.png", dpi=200)
