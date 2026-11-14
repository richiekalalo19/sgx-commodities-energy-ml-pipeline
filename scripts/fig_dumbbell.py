"""Figure 4: same-day versus Dimson (previous + same + next day) sensitivity, nine daily-mapped core counters.

Reads reports/tables/passthrough_daily.csv (written by scripts/11_passthrough_timing.py).
Run:  .venv/bin/python scripts/fig_dumbbell.py
Output: reports/figures/fig04_sameday_vs_dimson.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
d = pd.read_csv(root / "reports" / "tables" / "passthrough_daily.csv")
d = d[(d["group"] == "core") & (d["data_caveat"].isna())].sort_values("beta_dimson")

short = {"Brent (BZ=F)": "Brent", "gold (GC=F)": "gold", "coal (API2 Rotterdam)": "coal",
         "jet fuel (US Gulf spot)": "jet fuel"}
labels = [f"{n} ({short.get(u, u)})" for n, u in zip(d["name"], d["underlying"])]
y = np.arange(len(d))

fig, ax = plt.subplots(figsize=(8, 4.8))
ax.hlines(y, d["beta_same_day"], d["beta_dimson"], color="lightgrey", linewidth=2, zorder=1)
ax.scatter(d["beta_same_day"], y, color="tab:orange", s=40, zorder=2, label="Same-day regression")
ax.scatter(d["beta_dimson"], y, color="tab:blue", s=40, zorder=2, label="Dimson (previous + same + next day)")
ax.axvline(0, color="black", linewidth=0.8)

ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Sensitivity (% counter move per 1% commodity move)")
ax.grid(axis="x", linestyle=":", alpha=0.6)
ax.set_axisbelow(True)
ax.legend(loc="lower right", fontsize=9)

fig.tight_layout()
out = root / "reports" / "figures" / "fig04_sameday_vs_dimson.png"
fig.savefig(out, dpi=200)
print("saved", out)
print(d[["code", "beta_same_day", "beta_dimson"]].round(2).to_string(index=False))
