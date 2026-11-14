"""Exports the numbers the consultation deck charts, so the deck and the brief come from the same tables.

Output: consultation/deck_data.json
Run:  .venv/bin/python -I scripts/20_deck_data.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from fyp import config
from fyp.betas import equity_on_calendar, on_calendar, rolling_dimson
from fyp.panel import load
from fyp.power import mde_ic

T = config.TABLES
out: dict = {}

# Universe and costs: trading core counters, cheapest round trip first
lc = pd.read_csv(T / "liquidity_costs.csv")
core = lc[(lc["group"] == "core") & (lc["status"] == "trading")].sort_values("round_trip_floor_pct")
out["costs"] = dict(labels=[f"{n} ({c})" for n, c in zip(core["name"], core["code"])],
                    round_trip_pct=core["round_trip_floor_pct"].round(2).tolist(),
                    passes_100k=(core["median_value_sgd"] >= 100_000).tolist())
filt = pd.read_csv(T / "turnover_filter.csv")
out["filter"] = filt[["threshold_sgd", "counters_passing"]].to_dict("records")
out["n_trading_core"] = int(len(core))

# Timing: same-day against Dimson, counters with a reliable daily underlying
pt = pd.read_csv(T / "passthrough_daily.csv")
pt = pt[(pt["group"] == "core") & pt["data_caveat"].isna()].sort_values("beta_dimson")
out["timing"] = dict(labels=[f"{n} ({c})" for n, c in zip(pt["name"], pt["code"])],
                     same_day=pt["beta_same_day"].round(2).tolist(), dimson=pt["beta_dimson"].round(2).tolist(),
                     next_day_share=pt["next_day_share"].round(2).tolist())

# Drift: CNMC against gold, Kalman (month-end samples) and the rolling check
close, daily = load("equity_adjclose"), load("series_daily")
sgx = daily["sti"].dropna().index
sgx = sgx[sgx >= "2014-01-01"]
m = on_calendar(daily["sti"], sgx)
r = equity_on_calendar(close["5TP"], sgx)
c = on_calendar(daily["gold"], sgx)
kal = pd.read_csv(T / "kalman_5TP.csv", index_col=0, parse_dates=True)["beta_total_smoothed"].resample("ME").last()
roll = rolling_dimson(r, c, m).resample("ME").last().reindex(kal.index)
first = roll.first_valid_index()
kal, roll = kal.loc[first:], roll.loc[first:].ffill()   # charts cannot take gaps; months without a refit keep the last estimate
show = pd.read_csv(T / "kalman_showcase.csv").set_index("code")
out["drift"] = dict(labels=[d.strftime("%b %Y") for d in kal.index], kalman=kal.round(3).tolist(),
                    rolling=roll.round(3).tolist(),
                    start_2014=round(float(show.loc["5TP", "beta_start"]), 2),
                    end=round(float(show.loc["5TP", "beta_end"]), 2),
                    rex_min=round(float(show.loc["5WH", "beta_min"]), 2),
                    rex_max=round(float(show.loc["5WH", "beta_max"]), 2))

# How much is the commodity: weekly R-squared added
wk = pd.read_csv(T / "passthrough_weekly_r2.csv")
wk = wk[wk["code"].isin(config_codes := [x.code for x in config.CORE])].sort_values("added_by_commodity")
palm = {"F34", "E5H", "EB5", "P8Z"}
out["weekly_r2"] = dict(labels=[f"{n} ({c}){' *' if c in palm else ''}" for n, c in zip(wk["name"], wk["code"])],
                        added_pp=(100 * wk["added_by_commodity"]).round(1).tolist())
alpha = pd.read_csv(T / "plumbing_jensen_alpha.csv")
out["basket_r2"] = dict(sti_only=round(float(alpha.loc[0, "r2"]), 2), with_commodities=round(float(alpha.loc[1, "r2"]), 2))

# Export-ban events: first-session abnormal returns by group
lev = pd.read_csv(T / "levy_event_cars.csv")
d0 = lev[lev["window"] == "[0,+0]"].set_index("event_id")
groups = ["Indonesian growers, SGX", "Indonesian growers, IDX", "Malaysian growers, Bursa"]
events = [("E5", "Ban announced (25 Apr 2022)"), ("E6", "CPO added to ban (28 Apr)"), ("E7", "Lifting announced (20 May)")]
out["levy"] = dict(events=[lab for _, lab in events],
                   series=[dict(name=g, values=[round(100 * float(d0.loc[e, f"CAR {g}"]), 1) for e, _ in events])
                           for g in groups],
                   gap_ban=round(100 * float(d0.loc["E5", "gap SGX-Indonesian minus Malaysian"]), 1),
                   t_gap_ban=round(float(d0.loc["E5", "t gap"]), 1),
                   gap_lift=round(100 * float(d0.loc["E7", "gap SGX-Indonesian minus Malaysian"]), 1),
                   t_gap_lift=round(float(d0.loc["E7", "t gap"]), 1))

# Power curves
months = list(range(12, 181, 6))
out["power"] = dict(labels=[str(mm) for mm in months],
                    series=[dict(name=f"{n} counters", values=[round(mde_ic(n, mm), 3) for mm in months])
                            for n in (12, 18, 30)],
                    lockbox_18=round(mde_ic(18, 18), 2), wf_96=round(mde_ic(18, 96), 2), wf_120=round(mde_ic(18, 120), 2))

# Synthetic validation
syn = pd.read_csv(T / "synthetic_recovery.csv")
pw = pd.read_csv(T / "synthetic_ic_power.csv")
out["synthetic"] = dict(
    rmse_with_lag=round(float(syn["rmse_kalman_with_lag"].mean()), 2),
    rmse_same_day=round(float(syn["rmse_kalman_same_day"].mean()), 2),
    share_missed=round(float(1 - syn["mean_est_same_day"].mean() / syn["mean_truth"].mean()), 2),
    next_day_share_recovered=round(float(syn["dimson_next_day_share"].mean()), 2),
    asym_detected=int((syn["p_asym"] < 0.05).sum()), asym_runs=int(len(syn)),
    power_07_96=round(float(pw[(pw["months"] == 96) & (pw["ic"] == 0.07)]["power_mc"].iloc[0]), 2),
    false_pos_min=round(float(pw[pw["ic"] == 0.0]["power_mc"].min()), 3),
    false_pos_max=round(float(pw[pw["ic"] == 0.0]["power_mc"].max()), 3),
)

# Plumbing run: growth of S$100
bk = pd.read_csv(T / "plumbing_monthly.csv", index_col=0, parse_dates=True)
bench = daily["sti_etf"].dropna().resample("ME").last().pct_change().reindex(bk.index).fillna(0)
summ = pd.read_csv(T / "plumbing_summary.csv", index_col=0)
out["plumbing"] = dict(labels=[d.strftime("%b %Y") for d in bk.index],
                       basket=(100 * (1 + bk["net"]).cumprod()).round(1).tolist(),
                       sti=(100 * (1 + bench).cumprod()).round(1).tolist(),
                       sharpe_basket=round(float(summ.loc["Sector basket, net of costs", "sharpe_rf0"]), 2),
                       sharpe_sti=round(float(summ.loc["STI total return (ES3 ETF)", "sharpe_rf0"]), 2),
                       ret_basket=round(100 * float(summ.loc["Sector basket, net of costs", "annual_return"]), 1),
                       ret_sti=round(100 * float(summ.loc["STI total return (ES3 ETF)", "annual_return"]), 1),
                       dd_basket=round(100 * float(summ.loc["Sector basket, net of costs", "max_drawdown"]), 0),
                       alpha_capm=round(100 * float(alpha.loc[0, "alpha_annual"]), 1),
                       alpha_full=round(100 * float(alpha.loc[1, "alpha_annual"]), 1),
                       t_alpha_full=round(float(alpha.loc[1, "t_alpha"]), 1))

(config.CONSULT / "deck_data.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if not isinstance(vv, list)})
                  for k, v in out.items()}, indent=1))
