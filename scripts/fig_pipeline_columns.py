"""Figure 2 (column version): data pipeline as five stages, left to right.

Run:  .venv/bin/python scripts/fig_pipeline_columns.py
Output: reports/figures/fig02_pipeline_columns.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

stages = [
    ("Sources", ["Yahoo Finance:", "28 equities, 15 series,", "annual statements", "FRED: 8 series",
                 "SGX: securities list"], "whitesmoke"),
    ("Raw", ["One dated folder", "per download", "Never edited"], "whitesmoke"),
    ("Panel", ["Parquet tables", "Each market on its", "own calendar", "Holiday rows removed",
               "Fundamentals lagged", "60 days"], "whitesmoke"),
    ("Analyses", ["Liquidity and costs", "Pass-through timing", "Kalman residuals",
                  "Validation harness", "Sealed lockbox"], "aliceblue"),
    ("Outputs", ["CSV tables", "Figures"], "whitesmoke"),
]

fig, ax = plt.subplots(figsize=(10, 3.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.1)
ax.axis("off")

w, gap, y0, h = 1.65, 0.36, 0.15, 2.85
for i, (title, lines, colour) in enumerate(stages):
    x = 0.12 + i * (w + gap)
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.1",
                                facecolor=colour, edgecolor="grey", linewidth=1))
    ax.text(x + w / 2, y0 + h - 0.35, title, ha="center", va="center", fontsize=11, fontweight="bold")
    for j, line in enumerate(lines):
        ax.text(x + w / 2, y0 + h - 0.85 - j * 0.33, line, ha="center", va="center", fontsize=8.5)
    if i < len(stages) - 1:
        ax.annotate("", xy=(x + w + gap - 0.05, y0 + h / 2), xytext=(x + w + 0.05, y0 + h / 2),
                    arrowprops=dict(arrowstyle="-|>", color="tab:blue", lw=1.5))

fig.tight_layout()
out = Path(__file__).resolve().parents[1] / "reports" / "figures" / "fig02_pipeline_columns.png"
fig.savefig(out, dpi=200)
print("saved", out)
