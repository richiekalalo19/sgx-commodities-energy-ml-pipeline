"""Figure 2: data pipeline diagram (Stage 2).

Run:  .venv/bin/python scripts/fig_pipeline.py
Output: reports/figures/fig02_pipeline.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(10, 4.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4.2)
ax.axis("off")


def box(x, y, w, h, text, colour, sub=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=colour, edgecolor="black", linewidth=1))
    inside = sub and w < 1.5
    ax.text(x + w / 2, y + h / 2 + (0.1 if inside else 0), text, ha="center", va="center", fontsize=9.5,
            fontweight="bold")
    if inside:
        ax.text(x + w / 2, y + 0.13, sub, ha="center", va="center", fontsize=7.5, style="italic")
    elif sub:
        ax.text(x + w / 2, y - 0.12, sub, ha="center", va="top", fontsize=8)


def arrow(x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color="black", lw=1))


# sources
w, h = 1.6, 0.6
src = [(3.3, "Yahoo Finance", "tab:blue", "Prices, market series,\nannual statements"),
       (1.9, "FRED", "tab:cyan", "Rates, FX, monthly\nIMF commodity prices"),
       (0.5, "SGX", "tab:olive", "Securities list")]
for y, name, c, sub in src:
    box(0.2, y, w, h, name, c, sub)

# processing chain
chain = [(2.75, "Raw store\n(by date)", "lightgrey", None),
         (4.35, "Cleaning and\nalignment", "khaki", "SGX calendar"),
         (5.95, "Processed\npanel", "plum", "Parquet"),
         (7.55, "Residual\nseries", "lightsalmon", "Kalman filter"),
         ]
yc = 1.9
for x, name, c, sub in chain:
    box(x, yc, 1.3, 0.9, name, c, sub)

# sources -> raw store
xj = 2.35
for y, *_ in src:
    ax.plot([0.2 + w, xj], [y + h / 2, y + h / 2], color="black", lw=1)
ax.plot([xj, xj], [0.5 + h / 2, 3.3 + h / 2], color="black", lw=1)
yc = 1.9
arrow(xj, yc + 0.45, 2.75, yc + 0.45)

for (x0, *_), (x1, *_) in zip(chain[:-1], chain[1:]):
    arrow(x0 + 1.3, yc + 0.45, x1, yc + 0.45)

# harness and lockbox
box(7.55, 0.35, 1.3, 0.75, "Validation\nharness", "lightgreen")
box(9.0, 0.35, 0.9, 0.75, "Lockbox\n(sealed)", "lightgrey")
arrow(8.2, yc, 8.2, 1.1)
arrow(8.85, 0.725, 9.0, 0.725)

# fundamentals branch (point-in-time) feeding the panel
box(4.35, 0.35, 1.3, 0.85, "Point-in-time\nfundamentals", "wheat", "60-day lag")
arrow(5.0, yc, 5.0, 1.22)
ax.plot([5.65, 6.6], [0.775, 0.775], color="black", lw=1)
arrow(6.6, 0.775, 6.6, yc)

fig.tight_layout()
out = Path(__file__).resolve().parents[1] / "reports" / "figures" / "fig02_pipeline.png"
fig.savefig(out, dpi=200)
print("saved", out)
