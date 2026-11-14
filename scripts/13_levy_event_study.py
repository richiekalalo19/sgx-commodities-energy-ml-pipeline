"""Preliminary export-levy natural experiment (plan v2, section 6.5).

Indonesian export restrictions should lower what Indonesian growers receive relative to the
benchmark, while Malaysian growers sell at the benchmark. For each event in
data/reference/levy_events.csv this measures abnormal returns (market model against each
exchange's own index) for three equal-weight portfolios, and the exposed-minus-comparison gap.

Outputs: reports/tables/levy_event_cars.csv; figure levy_ban_2022.
Run:  .venv/bin/python -I scripts/13_levy_event_study.py
"""
from __future__ import annotations

import matplotlib.dates
import numpy as np
import pandas as pd

from fyp import config
from fyp.events import car_test, portfolio_ar
from fyp.panel import load, log_returns
from fyp.plotting import LINE_W, dots, figure, save, source, titles

close = load("equity_adjclose")
daily = load("series_daily")
rets = log_returns(close)
idx = log_returns(daily[["sti", "klci", "jkse"]])
palm = log_returns(daily[["palm"]])["palm"]

GROUPS = {
    "Indonesian growers, SGX": (["E5H", "EB5", "P8Z", "5JS"], "sti"),
    "Indonesian growers, IDX": (["AALI", "LSIP", "SIMP", "SSMS"], "jkse"),
    "Malaysian growers, Bursa": (["1961", "2445", "5285", "2291"], "klci"),
    "Wilmar (processor), SGX": (["F34"], "sti"),
}
events = pd.read_csv(config.REFERENCE / "levy_events.csv", parse_dates=["announced", "first_session"])


def signed(v: float, digits: int = 0) -> str:
    """Number with a true minus sign (or a plus sign) for labels."""
    return ("−" if v < 0 else "+" if v > 0 else "") + f"{abs(v):.{digits}f}"


def group_ar(group: str, event_date: str, post: int = 40):
    codes, ix = GROUPS[group]
    stocks = {c: (rets[c], idx[ix]) for c in codes if c in rets}
    return portfolio_ar(stocks, event_date, est_len=250, gap=30, pre=5, post=post)


rows = []
for _, ev in events.iterrows():
    d0 = ev["first_session"].strftime("%Y-%m-%d")
    res = {}
    for g in GROUPS:
        ar, sigma, used = group_ar(g, d0)
        if ar is None:
            continue
        sessions = ar.loc[d0:].index
        for k in (0, 1, 5):
            if len(sessions) > k:
                car, tval, n = car_test(ar, sigma, sessions[0], sessions[k])
                res[(g, k)] = (car, tval, sigma, n)
    palm_window = palm.loc[d0:].iloc[:6]
    for k in (0, 1, 5):
        row = dict(event_id=ev["event_id"], event=ev["event"], first_session=d0, window=f"[0,+{k}]",
                   expected_sign=ev["expected_sign_indonesian_growers"], confidence=ev["confidence"],
                   palm_futures_return=float(palm_window.iloc[:k + 1].sum()) if len(palm_window) > k else np.nan)
        for g in GROUPS:
            if (g, k) in res:
                row[f"CAR {g}"] = res[(g, k)][0]
                row[f"t {g}"] = res[(g, k)][1]
        exp_key, cmp_key = ("Indonesian growers, SGX", k), ("Malaysian growers, Bursa", k)
        if exp_key in res and cmp_key in res:
            (c1, _, s1, n1), (c2, _, s2, n2) = res[exp_key], res[cmp_key]
            row["gap SGX-Indonesian minus Malaysian"] = c1 - c2
            row["t gap"] = (c1 - c2) / np.sqrt(s1 ** 2 * n1 + s2 ** 2 * n2)
        rows.append(row)

tab = pd.DataFrame(rows)
config.TABLES.mkdir(parents=True, exist_ok=True)
tab.to_csv(config.TABLES / "levy_event_cars.csv", index=False)
pd.set_option("display.width", 250)
cols = ["event_id", "window", "expected_sign", "palm_futures_return", "CAR Indonesian growers, SGX",
        "t Indonesian growers, SGX", "CAR Indonesian growers, IDX", "CAR Malaysian growers, Bursa",
        "t Malaysian growers, Bursa", "gap SGX-Indonesian minus Malaysian", "t gap"]
print((tab[cols].set_index(["event_id", "window"]) * 1).round(3).to_string())

# Sign agreement over the high-confidence directional events, two-session window
hc = tab[(tab["window"] == "[0,+1]") & (tab["expected_sign"] != 0) &
         (tab["confidence"].str.startswith(("confirmed", "widely")))]
agree = (np.sign(hc["gap SGX-Indonesian minus Malaysian"]) == hc["expected_sign"]).sum()
print(f"\nHigh-confidence directional events: gap has the expected sign in {agree} of {len(hc)} "
      f"({', '.join(hc['event_id'])})")

# Figure: the 2022 export ban, cumulative abnormal returns by group
start, end = "2022-04-21", "2022-06-10"
paths = {}
for g in ["Indonesian growers, SGX", "Indonesian growers, IDX", "Malaysian growers, Bursa"]:
    ar, sigma, used = group_ar(g, "2022-04-25", post=45)
    path = ar.loc["2022-04-22":end].cumsum()
    paths[g] = pd.concat([pd.Series([0.0], index=[pd.Timestamp(start)]), path])
e5 = tab[(tab["event_id"] == "E5") & (tab["window"] == "[0,+0]")].iloc[0]
marks = [("2022-04-22", "Ban announced", "right"), ("2022-04-28", "Ban starts", "left"),
         ("2022-05-19", "Lifting announced", "right"), ("2022-05-23", "Ban ends", "left")]
for mode in ("light", "dark"):
    with figure(mode, w=8.6, h=4.8) as (fig, ax, t):
        colors = [t["s1"], t["s3"], t["s2"]]
        ax.axhline(0, color=t["axis"], linewidth=1.0, zorder=1)
        for x, label, side in marks:
            ax.axvline(pd.Timestamp(x), color=t["axis"], linewidth=1.0, zorder=1)
            ax.annotate(label, (matplotlib.dates.date2num(pd.Timestamp(x)), 1.0), xycoords=ax.get_xaxis_transform(),
                        xytext=(-4 if side == "right" else 4, 3), textcoords="offset points",
                        ha=side, va="bottom", fontsize=8.5, color=t["ink2"])
        for (g, path), color in zip(paths.items(), colors):
            ax.plot(path.index, 100 * path.values, color=color, linewidth=LINE_W, zorder=3, label=g)
            dots(ax, [path.index[-1]], [100 * path.values[-1]], color, t, size=6)
            ax.annotate(f"{signed(100 * path.values[-1])}%", (path.index[-1], 100 * path.values[-1]), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=9, color=t["ink2"])
        ax.set_ylabel("Cumulative abnormal return since 21 Apr 2022 (%)")
        ax.legend(loc="lower left", fontsize=9)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%-d %b"))
        ax.set_title(f"On the ban announcement, SGX-listed Indonesian growers fell {abs(100 * e5['CAR Indonesian growers, SGX']):.0f}% "
                     f"and Malaysian growers rose {100 * e5['CAR Malaysian growers, Bursa']:.0f}%", pad=40)
        ax.text(0, 1.085, f"First session, 25 Apr 2022. Gap {signed(100 * e5['gap SGX-Indonesian minus Malaysian'], 1)} points, "
                f"t = {signed(e5['t gap'], 1)}. Cumulative abnormal returns against each market's own index.",
                transform=ax.transAxes, fontsize=9.5, color=t["ink2"], va="bottom")
        source(fig, t, "Equal-weight portfolios. SGX: GAR, First Resources, Bumitama, IndoAgri. IDX: AALI, LSIP, SIMP, "
                       "SSMS. Bursa: IOI, KLK, SD Guthrie, Genting Plantations. Market model fitted on the 250 sessions "
                       "ending 30 sessions before 25 Apr 2022.")
        save(fig, "levy_ban_2022", mode)
