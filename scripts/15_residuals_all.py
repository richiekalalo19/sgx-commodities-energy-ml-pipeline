"""Aim 1 for every core counter: Kalman pass-through, the residual return series, and residual diagnostics.

Model (script 11's showcase model, plus a drifting market beta and a lagged market term):
    r_t = a + b0_t c_t + b1_t c_(t-1) + bm0_t m_t + bm1 m_(t-1) + e_t,   b0, b1 and bm0 drift as random walks
where c is the counter's daily commodity return and m the STI return. With a fixed market beta, four
counters kept significant same-day STI exposure in their residuals (Golden Agri t = -3.3); letting the
same-day beta drift removes it (all |t| < 1.7, checked 2026-11-10). The lagged term alone did not.
Counters without a usable daily commodity series get the market-only model
r_t = a + bm0_t m_t + bm1 m_(t-1) + e_t and are flagged:
  * palm counters, because CPO=F is a monthly-average swap (commodity term waits for Bloomberg FCPO);
  * counters with no traded underlying (energy infrastructure, Olam, Samudera).
The rolling one-year Dimson regression (plan task 9's benchmark) is computed for every counter with a
daily commodity series and drawn against the Kalman path.

Look-ahead control
  * Noise variances are estimated only on data before LOCKBOX_START; the filter then runs through the
    whole sample with them fixed, so nothing in the lockbox informs the model.
  * The residual uses the coefficients known at t-1: e_t = r_t - (b0 c_t + b1 c_(t-1) + bm0 m_t + bm1 m_(t-1)).
    The intercept stays in the residual.
  * Diagnostics use data before LOCKBOX_START only.

Outputs: data/processed/residuals_daily.parquet, reports/tables/kalman_all.csv,
         reports/tables/residual_diagnostics.csv, reports/tables/rolling_dimson_all.csv,
         figure kalman_all (light, dark)
Run:  .venv/bin/python -I scripts/15_residuals_all.py
"""
from __future__ import annotations

import warnings

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera

from fyp import config, kalman
from fyp.betas import equity_on_calendar, on_calendar, rolling_dimson
from fyp.panel import load
from fyp.plotting import figure, save, source

warnings.filterwarnings("ignore")

START = "2013-01-01"         # 2013 warms up the filter (plan v2); results are reported from 2014
REPORT_START = pd.Timestamp("2014-01-01")
# Lockbox start, fixed with the harness on 2026-11-10 (see src/fyp/harness.py).
LOCKBOX_START = pd.Timestamp("2025-05-01")
DAILY = {"brent": "brent", "gold": "gold", "jet": "jet", "coal": "coal"}
LABEL = {"brent": "Brent", "gold": "gold", "jet": "jet fuel", "coal": "coal (API2)"}
DRIFT_RANGE = 0.05           # a sensitivity "drifts" if its smoothed path spans at least this much

close = load("equity_adjclose")
volume = load("equity_volume")
daily = load("series_daily")
sgx = daily["sti"].dropna().index
sgx = sgx[sgx >= START]
m = on_calendar(daily["sti"], sgx)

summary, diags, resid, paths, rolls = [], [], {}, {}, {}
for c in config.CORE:
    if c.code not in close:
        continue
    r = equity_on_calendar(close[c.code], sgx)
    # Stop at the last day with real trading (Interra carries flat zero-volume rows after Jan 2025).
    traded = volume[c.code].where(volume[c.code] > 0).dropna().index
    r = r[r.index <= traded.max()]

    flags = []
    has_com = c.underlying in DAILY
    if has_com:
        cr = on_calendar(daily[DAILY[c.underlying]], sgx)
        df = pd.concat([r.rename("r"), cr.rename("c0"), cr.shift(1).rename("c1"),
                        m.rename("m0"), m.shift(1).rename("m1")], axis=1).dropna()
        X = np.column_stack([np.ones(len(df)), df["c0"], df["c1"], df["m0"], df["m1"]])
        varying, factors, mkt = [1, 2, 3], [1, 2, 3, 4], [3, 4]   # commodity terms and same-day STI drift
        model = f"{LABEL[c.underlying]} + STI"
        if c.underlying == "coal":
            flags.append("API2 Rotterdam proxy for Newcastle; series ends 26 Dec 2025")
        roll = rolling_dimson(r, cr, m)
        com_end = daily[DAILY[c.underlying]].dropna().index.max()      # API2 coal stops in Dec 2025
        rolls[c.code] = roll[(roll.index >= REPORT_START) & (roll.index <= com_end)]
    else:
        df = pd.concat([r.rename("r"), m.rename("m0"), m.shift(1).rename("m1")], axis=1).dropna()
        X = np.column_stack([np.ones(len(df)), df["m0"], df["m1"]])
        varying, factors, mkt = [1], [1, 2], [1, 2]                # same-day STI beta drifts
        model = "STI only"
        flags.append("commodity term waits for Bloomberg FCPO" if c.underlying == "palm" else "no traded underlying")
    if traded.max() < LOCKBOX_START:
        flags.append(f"inactive since {traded.max().date()}")

    pre = df.index < LOCKBOX_START
    est = kalman.fit(df["r"].values[pre], X[pre], varying=varying)
    run = kalman.filter_fixed(df["r"].values, X, est.q, est.r)
    known = np.vstack([run.b0, run.filtered[:-1]])               # coefficients known at t-1
    e = pd.Series(df["r"].values - np.sum(X[:, factors] * known[:, factors], axis=1), index=df.index)
    e = e[e.index >= REPORT_START]
    resid[c.code] = e

    row = dict(code=c.code, name=c.name, segment=c.segment, model=model, flag="; ".join(flags),
               first=e.index[0].date(), last=e.index[-1].date(), n=len(e), r=est.r, loglik=est.loglik)
    if has_com:
        total = pd.Series(run.smoothed[:, 1] + run.smoothed[:, 2], index=df.index)
        total = total[total.index >= REPORT_START]
        paths[c.code] = (c.name, LABEL[c.underlying], total)
        row.update(q_same_day=est.q[1], q_lag=est.q[2], beta_start=total.iloc[0], beta_end=total.iloc[-1],
                   beta_min=total.min(), beta_max=total.max(),
                   drifts=bool(total.max() - total.min() >= DRIFT_RANGE))
    row["beta_sti_end"] = run.smoothed[-1, mkt].sum()
    summary.append(row)

    # Diagnostics, pre-lockbox only
    d = df[pre & (df.index >= REPORT_START)].copy()
    d["e"] = e.reindex(d.index)
    dg = dict(code=c.code, name=c.name, model=model, n=len(d),
              variance_removed=1 - d["e"].var() / d["r"].var(),
              ac1=d["e"].autocorr(1),
              ljung_box_p10=float(acorr_ljungbox(d["e"], lags=[10], return_df=True)["lb_pvalue"].iloc[0]),
              arch_lm_p5=float(het_arch(d["e"], nlags=5)[1]),
              jarque_bera_p=float(jarque_bera(d["e"])[1]))
    fit_m = sm.OLS(d["e"], sm.add_constant(d[["m0", "m1"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    dg.update(sti_left=fit_m.params["m0"] + fit_m.params["m1"],
              t_sti_same=fit_m.tvalues["m0"], t_sti_lag=fit_m.tvalues["m1"])
    if has_com:
        fit_c = sm.OLS(d["e"], sm.add_constant(d[["c0", "c1"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        dg.update(commodity_left=fit_c.params["c0"] + fit_c.params["c1"],
                  t_commodity_same=fit_c.tvalues["c0"], t_commodity_lag=fit_c.tvalues["c1"])
    diags.append(dg)

config.PROCESSED.mkdir(parents=True, exist_ok=True)
pd.DataFrame(resid).to_parquet(config.PROCESSED / "residuals_daily.parquet")
summ = pd.DataFrame(summary)
summ.to_csv(config.TABLES / "kalman_all.csv", index=False)
dtab = pd.DataFrame(diags)
dtab.to_csv(config.TABLES / "residual_diagnostics.csv", index=False)
pd.DataFrame(rolls).to_csv(config.TABLES / "rolling_dimson_all.csv")
# Smoothed commodity sensitivity paths (same-day + next-day), for plain re-plotting (scripts/fig_kalman_all.py)
pd.DataFrame({code: s for code, (_, _, s) in paths.items()}).to_csv(config.TABLES / "kalman_paths_all.csv")

pd.set_option("display.width", 240)
print(f"Residual series for {len(resid)} core counters; lockbox starts {LOCKBOX_START.date()}\n")
print(summ[["code", "name", "model", "n", "last", "beta_start", "beta_end", "beta_min", "beta_max", "drifts", "flag"]]
      .round(2).to_string(index=False))
print("\nResidual diagnostics (pre-lockbox)")
print(dtab.round(3).to_string(index=False))

# Small multiples: Kalman path against the rolling one-year Dimson benchmark
order = sorted(paths, key=lambda k: -paths[k][2].iloc[-1])
n_drift = int(summ["drifts"].fillna(False).sum())
words = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
for mode in ("light", "dark"):
    with figure(mode, w=10.0, h=7.6) as (fig, ax0, t):
        ax0.remove()
        axes = fig.subplots(3, 3, sharex=True)
        for i, (ax, code) in enumerate(zip(axes.flat, order)):
            name, und, s = paths[code]
            if s.index[-1] > LOCKBOX_START:
                ax.axvspan(LOCKBOX_START, s.index[-1], color=t["band"], lw=0, zorder=0)
            ax.axhline(0, color=t["axis"], lw=0.8, zorder=1)
            if code in rolls:
                rl = rolls[code]
                ax.plot(rl.index, rl.values, color=t["muted"], linewidth=1.0, zorder=2,
                        label="Rolling 1-year Dimson" if i == 0 else None)
            ax.plot(s.index, s.values, color=t["s1"], linewidth=1.4, zorder=3,
                    label="Kalman, smoothed" if i == 0 else None)
            ax.set_title(f"{name} ({code}) vs {und}", fontsize=9, loc="left", pad=4, fontweight="bold")
            ax.annotate(f"{s.iloc[-1]:.2f}", (s.index[-1], s.iloc[-1]), xytext=(3, 0), textcoords="offset points",
                        fontsize=8, color=t["ink2"], va="center")
            ax.tick_params(labelsize=8)
            ax.xaxis.set_major_locator(mdates.YearLocator(4))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        for ax in list(axes.flat)[len(order):]:
            ax.axis("off")
        fig.legend(loc="upper right", bbox_to_anchor=(0.995, 1.035), ncols=2, fontsize=9, frameon=False)
        fig.text(0.01, 1.02, f"Commodity sensitivity drifts for {words[n_drift]} of the {words[len(order)]} counters "
                 "with a daily underlying", fontsize=13, weight="bold", color=t["ink"], ha="left", va="bottom")
        fig.text(0.01, 0.995, "Same-day plus next-day coefficient. Shaded: lockbox, not used to estimate the model.",
                 fontsize=9.5, color=t["ink2"], ha="left", va="bottom")
        fig.tight_layout()
        source(fig, t, "Daily log returns 2014 to Oct 2026 with the STI (same day and lagged) as control; 2013 warms up "
                       "the filter. Interra stops in Jan 2025; the API2 coal series (Geo Energy) stops in Dec 2025.")
        save(fig, "kalman_all", mode)
print(f"\n{n_drift} of {len(order)} daily-mapped counters drift (range >= {DRIFT_RANGE})")
print("wrote kalman_all figure, residuals_daily.parquet, kalman_all.csv, residual_diagnostics.csv, rolling_dimson_all.csv")
