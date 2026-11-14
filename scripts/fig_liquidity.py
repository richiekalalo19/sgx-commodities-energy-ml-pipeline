"""Figure 3: median daily traded value of the trading core counters, with the S$100k filter.

Reads reports/tables/liquidity_costs.csv (written by scripts/10_liquidity_costs.py).
Run:  .venv/bin/python scripts/fig_liquidity.py
Output: reports/figures/fig03_liquidity.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

root = Path(__file__).resolve().parents[1]
import pandas as pd  # noqa: E402

df = pd.read_csv(root / "reports" / "tables" / "liquidity_costs.csv")
df = df[(df["group"] == "core") & (df["status"] == "trading")].sort_values("median_value_sgd")

THRESH = 100_000
colours = ["tab:blue" if v >= THRESH else "lightgrey" for v in df["median_value_sgd"]]
labels = [f"{n} ({c})" for n, c in zip(df["name"], df["code"])]

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(labels, df["median_value_sgd"], color=colours, left=0)
ax.axvline(THRESH, color="tab:red", linestyle="--", linewidth=1.2)
ax.set_xscale("log")
ax.set_xlim(10_000, df["median_value_sgd"].max() * 2)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1e6:g}M" if v >= 1e6 else f"{v / 1e3:g}k"))
ax.set_xlabel("Median daily traded value, last 12 months (S$)")
ax.grid(axis="x", linestyle=":", alpha=0.6)
ax.set_axisbelow(True)

handles = [Patch(color="tab:blue", label="Above S$100k"), Patch(color="lightgrey", label="Below S$100k"),
           plt.Line2D([], [], color="tab:red", linestyle="--", label="S$100k filter")]
ax.legend(handles=handles, loc="lower right", fontsize=8)

fig.tight_layout()
out = root / "reports" / "figures" / "fig03_liquidity.png"
fig.savefig(out, dpi=200)
print("saved", out)
