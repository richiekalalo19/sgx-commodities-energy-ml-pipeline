"""Plumbing run (plan v2, interim chapter 4): an equal-weight sector basket through the cost model,
evaluated the way Aim 5 will evaluate a strategy. No signal is used and no lockbox is touched.

Monthly rebalance to equal weights across core counters that traded in the prior month. Costs per
counter per rebalance: half the tick-floored spread plus fees, on the weight actually traded.
Evaluation: annual return, volatility, Sharpe, drawdown, and Jensen's alpha against the STI total
return (ES3 ETF) plus Brent, gold and palm-oil factors, with HAC t-statistics.

Outputs: reports/tables/plumbing_*.csv; figure plumbing_basket.
Run:  .venv/bin/python -I scripts/14_basket_plumbing.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from fyp import config
from fyp.costs import fee_per_side, tick_size
from fyp.panel import load
from fyp.plotting import LINE_W, dots, figure, save, source, titles

START = "2014-01-01"
adj = load("equity_adjclose")
close = load("equity_close")
daily = load("series_daily")
monthly = load("series_monthly")
core = [c.code for c in config.CORE if c.code in adj]

month_end = adj.loc[START:].resample("ME").last()
traded = close.loc[START:].resample("ME").count() > 0
prices_me = close.loc[START:].resample("ME").last()
rets = month_end.pct_change()

weights_prev = pd.Series(0.0, index=core)
records = []
for i in range(1, len(month_end) - 1):
    t0, t1 = month_end.index[i], month_end.index[i + 1]
    eligible = [c for c in core if traded.loc[t0, c] and pd.notna(month_end.loc[t0, c])
                and pd.notna(rets.loc[t1, c])]
    target = pd.Series(0.0, index=core)
    target[eligible] = 1.0 / len(eligible)
    traded_w = (target - weights_prev).abs()
    px = prices_me.loc[t0, core]
    half_spread = 0.5 * pd.Series(tick_size(px.values), index=core) / px
    cost = float((traded_w * (half_spread.fillna(0) + fee_per_side())).sum())
    gross = float((target * rets.loc[t1, core].fillna(0)).sum())
    grown = target * (1 + rets.loc[t1, core].fillna(0))
    weights_prev = grown / grown.sum() if grown.sum() > 0 else target
    records.append(dict(month=t1, n=len(eligible), gross=gross, cost=cost, net=gross - cost,
                        turnover=float(traded_w.sum() / 2)))
bk = pd.DataFrame(records).set_index("month")

bench = daily["sti_etf"].dropna()
bench_m = bench.resample("ME").last().pct_change().reindex(bk.index)
sti_price_m = daily["sti"].resample("ME").last().pct_change().reindex(bk.index)


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    growth = (1 + r).cumprod()
    dd = growth / growth.cummax() - 1
    ann = (1 + r).prod() ** (12 / len(r)) - 1
    vol = r.std(ddof=1) * np.sqrt(12)
    return dict(months=len(r), annual_return=ann, volatility=vol, sharpe_rf0=ann / vol if vol else np.nan,
                max_drawdown=dd.min())


summary = pd.DataFrame({
    "Sector basket, net of costs": stats(bk["net"]),
    "Sector basket, before costs": stats(bk["gross"]),
    "STI total return (ES3 ETF)": stats(bench_m),
    "STI price index (no dividends)": stats(sti_price_m),
}).T
summary["avg_monthly_turnover"] = [bk["turnover"].mean(), bk["turnover"].mean(), np.nan, np.nan]
summary["avg_annual_cost"] = [bk["cost"].mean() * 12, 0.0, np.nan, np.nan]
config.TABLES.mkdir(parents=True, exist_ok=True)
summary.to_csv(config.TABLES / "plumbing_summary.csv")
bk.to_csv(config.TABLES / "plumbing_monthly.csv")

# Jensen's alpha with commodity factors (risk-free set to zero until a SORA or T-bill series is added)
fac = pd.DataFrame({
    "sti": bench_m,
    "brent": daily["brent"].resample("ME").last().pct_change().reindex(bk.index),
    "gold": daily["gold"].resample("ME").last().pct_change().reindex(bk.index),
    "palm": monthly["palm_m"].pct_change().set_axis(monthly.index + pd.offsets.MonthEnd(0)).reindex(bk.index),
})
rows = []
for label, cols in [("STI only (CAPM alpha)", ["sti"]), ("STI + Brent + gold + palm", ["sti", "brent", "gold", "palm"])]:
    df = pd.concat([bk["net"].rename("r"), fac[cols]], axis=1).dropna()
    fit = sm.OLS(df["r"], sm.add_constant(df[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    row = dict(model=label, months=int(fit.nobs), alpha_monthly=fit.params["const"],
               alpha_annual=(1 + fit.params["const"]) ** 12 - 1, t_alpha=fit.tvalues["const"], r2=fit.rsquared)
    for c in cols:
        row[f"beta_{c}"] = fit.params[c]
        row[f"t_{c}"] = fit.tvalues[c]
    rows.append(row)
alpha = pd.DataFrame(rows)
alpha.to_csv(config.TABLES / "plumbing_jensen_alpha.csv", index=False)

pd.set_option("display.width", 220)
print(summary.round(4).to_string())
print()
print(alpha.round(4).to_string(index=False))

growth_net = 100 * (1 + bk["net"]).cumprod()
growth_bench = 100 * (1 + bench_m.fillna(0)).cumprod()
for mode in ("light", "dark"):
    with figure(mode, w=8.0, h=4.3) as (fig, ax, t):
        ax.plot(growth_bench.index, growth_bench.values, color=t["muted"], linewidth=LINE_W,
                label="STI total return (ES3 ETF)")
        ax.plot(growth_net.index, growth_net.values, color=t["s1"], linewidth=LINE_W,
                label="Equal-weight sector basket, net of costs")
        for s, color in [(growth_net, t["s1"]), (growth_bench, t["muted"])]:
            dots(ax, [s.index[-1]], [s.iloc[-1]], color, t, size=6)
            ax.annotate(f"{s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=9, color=t["ink2"])
        ax.axhline(100, color=t["axis"], linewidth=1.0, zorder=1)
        ax.set_ylabel("Value of S$100 invested in Jan 2014")
        ax.legend(loc="upper left")
        a = alpha.iloc[1]
        titles(ax, t, "Plumbing check: a naive sector basket, costed and benchmarked",
               f"Jensen's alpha against the STI and commodity factors: {100 * a['alpha_annual']:+.1f}% a year "
               f"(t = {a['t_alpha']:.1f}). No signal is used; this tests the machinery.")
        source(fig, t, "Monthly rebalance to equal weights across core counters that traded in the month. Costs: half the "
                       "tick-floored spread plus SGX fees, brokerage and GST on each trade. Risk-free rate set to zero.")
        save(fig, "plumbing_basket", mode)
