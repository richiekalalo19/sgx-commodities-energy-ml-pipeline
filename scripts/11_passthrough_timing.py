"""Preliminary Aim 1: how much of each counter's return is its commodity, and when it arrives.

For every counter with a free daily underlying:
  * same-day OLS sensitivity against the Dimson (lag, same-day, lead) sensitivity
  * R-squared: STI alone, plus the commodity same-day, plus the Dimson terms
  * weekly up and down sensitivities (asymmetry), and a monthly check against IMF prices
  * Kalman-filtered sensitivity paths for two showcase counters

Outputs: reports/tables/passthrough_*.csv; figures passthrough_dumbbell, kalman_<code>.
Run:  .venv/bin/python -I scripts/11_passthrough_timing.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from fyp import config, kalman
from fyp.betas import asymmetric, dimson, equity_on_calendar, on_calendar, rolling_dimson
from fyp.panel import load
from fyp.plotting import LINE_W, dots, figure, save, source, titles

warnings.filterwarnings("ignore")

UNDERLYING = {"palm": "palm", "brent": "brent", "gold": "gold", "jet": "jet", "coal": "coal"}
LABEL = {"palm": "palm oil (CPO=F)", "brent": "Brent (BZ=F)", "gold": "gold (GC=F)",
         "jet": "jet fuel (US Gulf spot)", "coal": "coal (API2 Rotterdam)"}
START = "2014-01-01"

close = load("equity_adjclose")
daily = load("series_daily")
monthly = load("series_monthly")
sgx = daily["sti"].dropna().index
sgx = sgx[sgx >= START]
m = on_calendar(daily["sti"], sgx)
fx = on_calendar(daily["usdsgd"], sgx)

rows, asym_rows, cache = [], [], {}
for c in config.UNIVERSE:
    if c.exchange != "SGX" or c.group not in ("core", "levy-exposed") or c.underlying not in UNDERLYING:
        continue
    if c.code not in close:
        continue
    key = UNDERLYING[c.underlying]
    r = equity_on_calendar(close[c.code], sgx)
    cr = on_calendar(daily[key], sgx)
    res = dimson(r, cr, m, fx)
    res.update(code=c.code, name=c.name, group=c.group, underlying=LABEL[c.underlying])
    res["next_day_share"] = res["beta_lag"] / res["beta_dimson"] if res["beta_dimson"] > 0 else np.nan
    rows.append(res)
    a = asymmetric(r, cr, m)
    a.update(code=c.code, name=c.name, underlying=LABEL[c.underlying])
    asym_rows.append(a)
    cache[c.code] = (r, cr)

tab = pd.DataFrame(rows)
# CPO=F is the CME palm-oil calendar future, settled on the monthly average of Bursa FCPO: its daily
# changes are damped within the month and jump at each roll, so daily palm betas are biased low.
tab["data_caveat"] = np.where(tab["underlying"].str.startswith("palm"),
                              "CPO=F is a monthly-average swap: daily beta biased low; use Bloomberg FCPO", "")
order = ["code", "name", "group", "underlying", "n", "beta_same_day", "t_same_day", "beta_lag", "t_lag",
         "beta_lead", "t_lead", "beta_dimson", "t_dimson", "next_day_share", "r2_market", "r2_same_day", "r2_dimson",
         "data_caveat"]
tab = tab[order].sort_values("beta_dimson", ascending=False)

# Robustness for the Brent counters: FRED Brent spot has no futures rolls
spot = on_calendar(daily["brent_spot"], sgx)
spot_rows = []
for code, (r, cr) in cache.items():
    if not tab.loc[tab["code"] == code, "underlying"].iloc[0].startswith("Brent"):
        continue
    s = dimson(r, spot, m, fx)
    f = tab.loc[tab["code"] == code].iloc[0]
    spot_rows.append(dict(code=code, beta_dimson_futures=f["beta_dimson"], beta_dimson_spot=s["beta_dimson"],
                          next_day_share_futures=f["next_day_share"],
                          next_day_share_spot=s["beta_lag"] / s["beta_dimson"] if s["beta_dimson"] > 0 else np.nan))
pd.DataFrame(spot_rows).to_csv(config.TABLES / "passthrough_brent_spot_check.csv", index=False)
print("Brent futures (BZ=F) against Brent spot (FRED) as the underlying")
print(pd.DataFrame(spot_rows).round(3).to_string(index=False), "\n")
tab.to_csv(config.TABLES / "passthrough_daily.csv", index=False)
asym = pd.DataFrame(asym_rows)[["code", "name", "underlying", "n_weeks", "beta_up", "t_up", "beta_down", "t_down",
                                 "diff", "t_diff", "p_diff"]]
asym.to_csv(config.TABLES / "passthrough_asymmetry_weekly.csv", index=False)

pd.set_option("display.width", 220)
print("Daily pass-through, 2014 onward (HAC t-stats)")
print(tab.drop(columns=["group"]).round(3).to_string(index=False))
print("\nWeekly asymmetry (up minus down)")
print(asym.round(3).to_string(index=False))

# Monthly check against the IMF monthly averages for palm oil and coal
mrows = []
sti_m = np.log(daily["sti"].resample("ME").last()).diff()
for code, key in [("F34", "palm_m"), ("E5H", "palm_m"), ("EB5", "palm_m"), ("P8Z", "palm_m"), ("5JS", "palm_m"),
                  ("RE4", "coal_m")]:
    eq = np.log(close[code].dropna().resample("ME").last()).diff()
    com = np.log(monthly[key]).diff()
    com.index = com.index + pd.offsets.MonthEnd(0)
    df = pd.concat([eq.rename("r"), com.rename("c"), sti_m.rename("m")], axis=1).loc[START:].dropna()
    import statsmodels.api as sm
    fit = sm.OLS(df["r"], sm.add_constant(df[["c", "m"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    fit_m = sm.OLS(df["r"], sm.add_constant(df[["m"]])).fit()
    mrows.append(dict(code=code, series=key, months=len(df), beta=fit.params["c"], t=fit.tvalues["c"],
                      r2_market=fit_m.rsquared, r2_with_commodity=fit.rsquared))
mon = pd.DataFrame(mrows)
mon.to_csv(config.TABLES / "passthrough_monthly_imf.csv", index=False)
print("\nMonthly check against IMF prices")
print(mon.round(3).to_string(index=False))

# How much of the return is the commodity? Weekly R-squared, where tick noise and closing times matter less
wrows = []
for code, (r, cr) in cache.items():
    rw = r.resample("W-FRI").sum(min_count=1)
    cw = cr.resample("W-FRI").sum(min_count=1)
    mw = m.resample("W-FRI").sum(min_count=1)
    df = pd.concat([rw.rename("r"), cw.rename("c"), cw.shift(1).rename("c1"), mw.rename("m")], axis=1).dropna()
    import statsmodels.api as sm
    r2_m = sm.OLS(df["r"], sm.add_constant(df[["m"]])).fit().rsquared
    r2_c = sm.OLS(df["r"], sm.add_constant(df[["m", "c", "c1"]])).fit().rsquared
    r2_c_only = sm.OLS(df["r"], sm.add_constant(df[["c", "c1"]])).fit().rsquared
    name = tab.loc[tab["code"] == code, "name"].iloc[0]
    wrows.append(dict(code=code, name=name, weeks=len(df), r2_sti=r2_m, r2_commodity_only=r2_c_only,
                      r2_sti_plus_commodity=r2_c, added_by_commodity=r2_c - r2_m))
wk = pd.DataFrame(wrows).sort_values("added_by_commodity", ascending=False)
wk.to_csv(config.TABLES / "passthrough_weekly_r2.csv", index=False)
print("\nWeekly R-squared: how much of the return the commodity explains")
print(wk.round(3).to_string(index=False))

# Figure: same-day against Dimson sensitivity, one dumbbell per counter
plot = tab[(tab["group"] == "core") & (tab["data_caveat"] == "")].sort_values("beta_dimson")
for mode in ("light", "dark"):
    with figure(mode, w=8.0, h=5.2) as (fig, ax, t):
        y = np.arange(len(plot))
        ax.hlines(y, plot["beta_same_day"], plot["beta_dimson"], color=t["axis"], linewidth=2.0, zorder=2)
        dots(ax, plot["beta_same_day"], y, t["s1_soft"], t, label="Same-day OLS")
        dots(ax, plot["beta_dimson"], y, t["s1"], t, label="Dimson (lag + same day + lead)")
        ax.axvline(0, color=t["axis"], linewidth=1.0, zorder=1)
        ax.set_yticks(y, [f"{n} ({c})\nvs {u}" for n, c, u in zip(plot["name"], plot["code"], plot["underlying"])],
                      fontsize=9)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("Sensitivity to a 1% commodity move (% move in the counter)")
        last = plot.iloc[-1]
        ax.annotate(f"{last['beta_same_day']:.2f}", (last["beta_same_day"], y[-1]), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
        ax.annotate(f"{last['beta_dimson']:.2f}", (last["beta_dimson"], y[-1]), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8.5, color=t["ink2"])
        ax.legend(loc="lower right", handletextpad=0.3)
        titles(ax, t, "Same-day regressions understate pass-through",
               "Adding the next-day term raises the measured sensitivity for every counter shown")
        source(fig, t, "Daily log returns 2014 to Oct 2026, STI and USD/SGD as controls. Yahoo Finance (BZ=F, GC=F, MTF=F), "
                       "FRED (jet fuel). Palm counters omitted: the free daily palm series (CPO=F) is a monthly-average swap.")
        save(fig, "passthrough_dumbbell", mode)

# Kalman-filtered sensitivity for two showcase counters, with the rolling Dimson estimate as the check
show = [("5TP", "CNMC Goldmine", "gold"), ("5WH", "Rex International", "Brent")]
kal_rows = []
for code, name, com_name in show:
    r, cr = cache[code]
    df = pd.concat([r.rename("r"), cr.rename("c0"), cr.shift(1).rename("c1"), m.rename("m")], axis=1).dropna()
    X = np.column_stack([np.ones(len(df)), df["c0"], df["c1"], df["m"]])
    res = kalman.fit(df["r"].values, X, varying=[1, 2])
    total = pd.Series(res.smoothed[:, 1] + res.smoothed[:, 2], index=df.index)
    roll = rolling_dimson(r, cr, m)
    kal_rows.append(dict(code=code, q_same_day=res.q[1], q_lag=res.q[2], r=res.r, loglik=res.loglik,
                         beta_start=total.iloc[0], beta_end=total.iloc[-1], beta_min=total.min(), beta_max=total.max()))
    total.to_csv(config.TABLES / f"kalman_{code}.csv", header=["beta_total_smoothed"])
    for mode in ("light", "dark"):
        with figure(mode, w=8.0, h=4.2) as (fig, ax, t):
            ax.plot(roll.index, roll.values, color=t["muted"], linewidth=LINE_W, label="Rolling 1-year Dimson")
            ax.plot(total.index, total.values, color=t["s1"], linewidth=LINE_W, label="Kalman, smoothed")
            ax.axhline(0, color=t["axis"], linewidth=1.0, zorder=1)
            end = total.index[-1]
            ax.annotate(f"{total.iloc[-1]:.2f}", (end, total.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=9, color=t["ink2"])
            dots(ax, [end], [total.iloc[-1]], t["s1"], t, size=6)
            ax.set_ylabel("Sensitivity (same day + next day)")
            ax.legend(loc="best", ncols=2)
            titles(ax, t, f"{name}: sensitivity to {com_name}, {total.iloc[0]:.2f} in 2014 to {total.iloc[-1]:.2f} now",
                   f"Kalman estimate ranges {total.min():.2f} to {total.max():.2f}; the rolling window is far noisier")
            source(fig, t, "Daily log returns with STI as control. Sensitivity = same-day plus next-day coefficient.")
            save(fig, f"kalman_{code}", mode)
pd.DataFrame(kal_rows).to_csv(config.TABLES / "kalman_showcase.csv", index=False)
print("\nKalman showcase")
print(pd.DataFrame(kal_rows).round(5).to_string(index=False))
