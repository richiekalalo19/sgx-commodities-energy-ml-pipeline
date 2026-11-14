"""Liquidity and trading cost per counter: the evidence for the turnover filter and the cost model.

Outputs: reports/tables/liquidity_costs.csv, turnover_filter.csv; figure liquidity_dots_{light,dark}.
Run:  .venv/bin/python -I scripts/10_liquidity_costs.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fyp import config
from fyp.costs import amihud, corwin_schultz, fee_per_side, round_trip_cost, tick_size
from fyp.panel import load, load_yahoo
from fyp.plotting import dots, figure, save, source, titles

close, high, low, vol = (load(f"equity_{k}") for k in ("close", "high", "low", "volume"))
sgx_days = load("series_daily")["sti"].dropna().index
asof = sgx_days.max()
start12 = asof - pd.DateOffset(months=12)
window = sgx_days[sgx_days > start12]

rows = []
for c in config.UNIVERSE:
    if c.exchange != "SGX" or c.code not in close:
        continue
    p = close[c.code].dropna()
    last_trade = p.index.max()
    suspended = (asof - last_trade).days > 30
    raw = load_yahoo(c.yahoo)
    traded = raw["Volume"].reindex(window).fillna(0) > 0
    value = (close[c.code] * vol[c.code]).reindex(window).fillna(0)
    cs = corwin_schultz(high[c.code], low[c.code], close[c.code]).loc[start12:]
    ret = np.log(p).diff().loc[start12:]
    price = float(p.iloc[-1])
    rows.append(dict(
        code=c.code, name=c.name, segment=c.segment, group=c.group,
        last_trade=last_trade.date(), status="suspended or inactive" if suspended else "trading",
        last_price=price, tick=float(tick_size(price)), tick_pct=100 * float(tick_size(price)) / price,
        round_trip_floor_pct=100 * float(round_trip_cost(price)),
        cs_spread_pct=100 * float(cs.resample("ME").mean().median()) if cs.notna().any() else np.nan,
        no_trade_days_pct=100 * (1 - traded.mean()),
        median_value_sgd=float(value.median()), mean_value_sgd=float(value.mean()),
        amihud=amihud(ret, (close[c.code] * vol[c.code]).loc[start12:]),
    ))
tab = pd.DataFrame(rows).sort_values("median_value_sgd", ascending=False)
config.TABLES.mkdir(parents=True, exist_ok=True)
tab.to_csv(config.TABLES / "liquidity_costs.csv", index=False)

core = tab[tab["group"] == "core"]
thresholds = [50_000, 100_000, 250_000, 500_000, 1_000_000]
filt = pd.DataFrame([dict(
    threshold_sgd=th,
    counters_passing=int(((core["median_value_sgd"] >= th) & (core["status"] == "trading")).sum()),
    names=", ".join(core.loc[(core["median_value_sgd"] >= th) & (core["status"] == "trading"), "code"]),
) for th in thresholds])
filt.to_csv(config.TABLES / "turnover_filter.csv", index=False)

print(f"As of {asof.date()} · fee per side {100 * fee_per_side():.3f}%")
show = ["code", "name", "status", "last_price", "tick_pct", "round_trip_floor_pct", "cs_spread_pct",
        "no_trade_days_pct", "median_value_sgd", "amihud"]
print(tab[show].round(3).to_string(index=False))
print()
print(filt.to_string(index=False))

# Figure: median daily traded value, dots on a log axis, filter line at S$100k
THRESH = 100_000
plot = core[core["status"] == "trading"].sort_values("median_value_sgd")
for mode in ("light", "dark"):
    with figure(mode, w=8.0, h=6.2) as (fig, ax, t):
        y = np.arange(len(plot))
        passing = plot["median_value_sgd"] >= THRESH
        ax.hlines(y, plot["median_value_sgd"].clip(lower=1_000), 1_000, color=t["grid"], linewidth=0.8, zorder=1)
        dots(ax, plot.loc[passing, "median_value_sgd"], y[passing.values], t["s1"], t)
        dots(ax, plot.loc[~passing, "median_value_sgd"].clip(lower=1_000), y[~passing.values], t["muted"], t)
        ax.axvline(THRESH, color=t["ink2"], linewidth=1.0, zorder=2)
        ax.text(THRESH * 1.08, len(plot) - 0.6, "S$100k filter", color=t["ink2"], fontsize=9, va="center")
        ax.set_xscale("log")
        ax.set_xlim(1_000, plot["median_value_sgd"].max() * 3)
        ax.set_yticks(y, [f"{n} ({c})" for n, c in zip(plot["name"], plot["code"])])
        ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_formatter(lambda v, _: f"S${v / 1e6:g}M" if v >= 1e6 else f"S${v / 1e3:g}k")
        ax.tick_params(axis="y", length=0)
        titles(ax, t, "Median daily traded value, last 12 months",
               f"{int(passing.sum())} of {len(plot)} trading counters clear S$100k a day; grey dots fall below it")
        source(fig, t, f"Source: Yahoo Finance daily close × volume on SGX trading days to {asof.date()}. "
                       "Interra Resources (5GI) has not traded since 31 Jan 2025 and is excluded.")
        save(fig, "liquidity_dots", mode)
