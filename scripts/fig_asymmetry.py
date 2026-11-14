"""Figure: weekly sensitivity in rising versus falling commodity weeks, nine daily-mapped core counters.

Reads reports/tables/passthrough_asymmetry_weekly.csv (written by scripts/11_passthrough_timing.py).
Palm counters are left out because the free daily palm series (CPO=F) is unreliable.
Run:  .venv/bin/python scripts/fig_asymmetry.py
Output: reports/figures/fig_asymmetry.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
a = pd.read_csv(root / "reports" / "tables" / "passthrough_asymmetry_weekly.csv")
core9 = ["5TP", "5GI", "5WH", "T13", "DU4", "RE4", "5E2", "5LY", "G92"]
a = a[a["code"].isin(core9)].sort_values("beta_up")

y = np.arange(len(a))
h = 0.38
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(y + h / 2, a["beta_up"], height=h, color="tab:green", label="Rising commodity weeks")
ax.barh(y - h / 2, a["beta_down"], height=h, color="tab:red", label="Falling commodity weeks")
ax.axvline(0, color="black", linewidth=0.8)

labels = [f"{n} ({c})" + ("  *" if p < 0.05 else "") for n, c, p in zip(a["name"], a["code"], a["p_diff"])]
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Weekly sensitivity (% counter move per 1% commodity move)")
ax.grid(axis="x", linestyle=":", alpha=0.6)
ax.set_axisbelow(True)
ax.legend(loc="lower right", fontsize=9)

fig.tight_layout()
out = root / "reports" / "figures" / "fig_asymmetry.png"
fig.savefig(out, dpi=200)
print("saved", out)
print(a[["code", "beta_up", "beta_down", "p_diff"]].round(3).to_string(index=False))
