"""Figure 1: project timeline (Gantt chart of the seven stages).

Run:  .venv/bin/python scripts/fig_timeline.py
Output: reports/figures/fig01_timeline.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Week index: S1 W1-W7 = 1-7, recess = 8, S1 W8-W13 = 9-14, break = 15-20,
# S2 W1-W13 = 21-33, S2 exam weeks = 34-35
stages = [
    ("Groundwork", 1, 10, "Done"),
    ("Data and infrastructure", 6, 13, "In progress"),
    ("Aim 1: Pass-through", 11, 14, "In progress"),
    ("Aims 2-3: FA and NA", 15, 26, "Planned"),
    ("Aim 4: Model comparison", 24, 29, "Planned"),
    ("Aim 5: Strategy", 28, 31, "Planned"),
    ("Reporting", 28, 35, "Planned"),
]
colours = {"Done": "tab:green", "In progress": "tab:blue", "Planned": "lightsteelblue"}

fig, ax = plt.subplots(figsize=(9, 4))
for i, (name, start, end, status) in enumerate(stages):
    ax.barh(i, end - start + 1, left=start - 0.5, height=0.6, color=colours[status])

ax.axvline(14, color="tab:red", linestyle="--", linewidth=1.2)

ax.set_yticks(range(len(stages)))
ax.set_yticklabels([s[0] for s in stages])
ax.invert_yaxis()
ax.set_xticks([1, 4, 8, 11, 14, 17.5, 21, 25, 29, 34.5])
ax.set_xticklabels(["S1 W1", "W4", "Recess", "W10", "W13", "Break", "S2 W1", "W5", "W9", "Exams"])
ax.set_xlim(0.3, 35.7)
ax.set_xlabel("Academic week")
ax.grid(axis="x", linestyle=":", alpha=0.6)
ax.set_axisbelow(True)

handles = [Patch(color=c, label=s) for s, c in colours.items()]
handles.append(plt.Line2D([], [], color="tab:red", linestyle="--", label="Interim report"))
ax.legend(handles=handles, loc="lower left", fontsize=8)

fig.tight_layout()
out = Path(__file__).resolve().parents[1] / "reports" / "figures" / "fig01_timeline.png"
fig.savefig(out, dpi=200)
print("saved", out)
