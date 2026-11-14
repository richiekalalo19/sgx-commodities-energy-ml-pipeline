"""Synthetic ground truth (plan v2, section 6.2).

1. A counter with a planted drifting sensitivity, a 40% next-day share, falls transmitting
   30% more strongly, fat tails and 15% no-trade days. Checks that the Kalman filter with the
   next-day term recovers the path, and how far a same-day-only filter falls short.
2. The monthly information-coefficient test with 18 names: Monte Carlo power and false-positive
   rate, against the analytic detectable-effect table in the plan.

Outputs: reports/tables/synthetic_*.csv; figures synthetic_recovery, power_curve.
Run:  .venv/bin/python -I scripts/12_synthetic_validation.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fyp import config, kalman
from fyp.betas import asymmetric, dimson
from fyp.plotting import LINE_W, dots, figure, save, source, titles
from fyp.power import mde_ic
from fyp.synthetic import ic_power, simulate_counter

# 1. Kalman recovery over several seeds
rec_rows = []
for seed in range(5):
    sim = simulate_counter(seed=seed)
    y = sim["r"].values
    X2 = np.column_stack([np.ones(len(sim)), sim["c"], sim["c"].shift(1).fillna(0), sim["m"]])
    X1 = np.column_stack([np.ones(len(sim)), sim["c"], sim["m"]])
    full = kalman.fit(y, X2, varying=[1, 2])
    same = kalman.fit(y, X1, varying=[1])
    est_full = full.smoothed[:, 1] + full.smoothed[:, 2]
    est_same = same.smoothed[:, 1]
    # True total sensitivity: beta_t on the up side; falls carry 30% more
    truth = sim["beta_true"].values
    burn = 120
    rmse_full = float(np.sqrt(np.mean((est_full[burn:] - truth[burn:]) ** 2)))
    rmse_same = float(np.sqrt(np.mean((est_same[burn:] - truth[burn:]) ** 2)))
    d = dimson(sim["r"], sim["c"], sim["m"])
    a = asymmetric(sim["r"], sim["c"], sim["m"])
    rec_rows.append(dict(seed=seed, rmse_kalman_with_lag=rmse_full, rmse_kalman_same_day=rmse_same,
                         mean_truth=float(truth.mean()), mean_est_with_lag=float(est_full.mean()),
                         mean_est_same_day=float(est_same.mean()),
                         dimson_next_day_share=d["beta_lag"] / d["beta_dimson"],
                         weekly_beta_up=a["beta_up"], weekly_beta_down=a["beta_down"], p_asym=a["p_diff"]))
    if seed == 0:
        keep = (sim.index, truth, est_full, est_same)
rec = pd.DataFrame(rec_rows)
config.TABLES.mkdir(parents=True, exist_ok=True)
rec.to_csv(config.TABLES / "synthetic_recovery.csv", index=False)
print("Kalman recovery (planted next-day share 0.40; falls 30% stronger)")
print(rec.round(3).to_string(index=False))
print(rec.drop(columns="seed").mean().round(3).to_string())

idx, truth, est_full, est_same = keep
for mode in ("light", "dark"):
    with figure(mode, w=8.0, h=4.2) as (fig, ax, t):
        ax.plot(idx, truth, color=t["ink2"], linewidth=LINE_W, label="Planted sensitivity")
        ax.plot(idx, est_full, color=t["s1"], linewidth=LINE_W, label="Kalman with next-day term")
        ax.plot(idx, est_same, color=t["s2"], linewidth=LINE_W, label="Kalman, same day only")
        for series, color in [(est_full, t["s1"]), (est_same, t["s2"])]:
            dots(ax, [idx[-1]], [series[-1]], color, t, size=6)
            ax.annotate(f"{series[-1]:.2f}", (idx[-1], series[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=9, color=t["ink2"])
        ax.set_ylabel("Sensitivity")
        ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.16))
        r0 = rec.iloc[0]
        titles(ax, t, "Without the next-day term the filter misses about 40% of the response",
               f"Error {r0['rmse_kalman_with_lag']:.2f} with it, {r0['rmse_kalman_same_day']:.2f} without. "
               "At this noise level it recovers the level but not the slow drift.")
        source(fig, t, "Simulated counter: drifting sensitivity, 40% next-day share, t(4) noise, 15% no-trade days.")
        save(fig, "synthetic_recovery", mode)

# 2. Power of the monthly IC test with 18 names
grid = []
for months in (18, 60, 96, 120):
    for ic in (0.0, 0.03, 0.05, 0.07, 0.10):
        grid.append(dict(months=months, ic=ic, power_mc=ic_power(18, months, ic, n_sims=3000, seed=months),
                         mde_analytic=mde_ic(18, months)))
pw = pd.DataFrame(grid)
pw.to_csv(config.TABLES / "synthetic_ic_power.csv", index=False)
print("\nIC test, 18 names: Monte Carlo rejection rate (IC = 0 is the false-positive rate)")
print(pw.pivot(index="months", columns="ic", values="power_mc").round(3).to_string())

months = np.arange(12, 181)
for mode in ("light", "dark"):
    with figure(mode, w=8.0, h=4.4) as (fig, ax, t):
        ax.axhspan(0.02, 0.05, color=t["band"], zorder=0)
        ax.text(16, 0.035, "typical real signals, 0.02 to 0.05", ha="left", va="center", fontsize=9, color=t["ink2"])
        for n, color, lw in [(12, t["muted"], 1.2), (30, t["muted"], 1.2), (18, t["s1"], LINE_W)]:
            ax.plot(months, [mde_ic(n, mm) for mm in months], color=color, linewidth=lw, zorder=2)
            ax.annotate(f"{n} counters", (180, mde_ic(n, 180)), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=9, color=t["ink2"])
        label_at = {18: (34, 0.215), 96: (112, 0.175), 120: (140, 0.14)}
        for mm, label in [(18, "18-month lockbox"), (96, "8 years"), (120, "10 years")]:
            v = mde_ic(18, mm)
            dots(ax, [mm], [v], t["s1"], t)
            ax.annotate(f"{label}: {v:.2f}", (mm, v), xytext=label_at[mm], textcoords="data", fontsize=9,
                        color=t["ink"], arrowprops=dict(arrowstyle="-", color=t["muted"], linewidth=0.8,
                                                        shrinkA=2, shrinkB=5))
        ax.set_xlim(10, 200)
        ax.set_ylim(0, 0.32)
        ax.set_xlabel("Months of out-of-sample data")
        ax.set_ylabel("Smallest detectable IC")
        titles(ax, t, "An 18-month lockbox can only detect implausibly strong signals",
               "Smallest monthly information coefficient detectable with 80% power at the 5% level")
        source(fig, t, "Analytic: 2.8 / sqrt(N - 1) / sqrt(T). Monte Carlo check in reports/tables/synthetic_ic_power.csv.")
        save(fig, "power_curve", mode)
