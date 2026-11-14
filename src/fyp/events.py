"""Market-model event studies, with portfolio aggregation for events that hit many counters at once.

Each stock is measured against its own exchange's index on its own trading calendar. Stocks
hit by the same announcement are averaged into one portfolio before testing, so a
sector-wide event counts once (Brown and Warner, 1985), not once per counter.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def abnormal_returns(r: pd.Series, rm: pd.Series, event_date: str, est_len: int = 250, gap: int = 30,
                     pre: int = 5, post: int = 40) -> tuple[pd.Series, pd.Series] | None:
    """AR by calendar date over [-pre, +post] sessions, plus estimation-window residuals.

    Day 0 is the first session on or after `event_date`.
    """
    data = pd.concat([r.rename("r"), rm.rename("m")], axis=1).dropna()
    if data.empty:
        return None
    pos = data.index.searchsorted(pd.Timestamp(event_date))
    if pos - gap - est_len < 0 or pos >= len(data):
        return None
    est = data.iloc[pos - gap - est_len: pos - gap]
    fit = sm.OLS(est["r"], sm.add_constant(est["m"])).fit()
    win = data.iloc[max(pos - pre, 0): pos + post + 1]
    ar = win["r"] - (fit.params["const"] + fit.params["m"] * win["m"])
    return ar, fit.resid


def portfolio_ar(stocks: dict[str, tuple[pd.Series, pd.Series]], event_date: str, **kw):
    """Equal-weight portfolio AR (by date) and the std of the portfolio's estimation residuals."""
    ars, resids = {}, {}
    for name, (r, rm) in stocks.items():
        out = abnormal_returns(r, rm, event_date, **kw)
        if out is None:
            continue
        ars[name], resids[name] = out
    if not ars:
        return None, np.nan, []
    ar = pd.DataFrame(ars).mean(axis=1)
    sigma = pd.DataFrame(resids).mean(axis=1).std(ddof=1)
    return ar, sigma, list(ars)


def car_test(ar: pd.Series, sigma: float, start: str, end: str) -> tuple[float, float, int]:
    """CAR between two dates (inclusive) and its t-statistic."""
    window = ar.loc[start:end].dropna()
    n = len(window)
    car = float(window.sum())
    return car, (car / (sigma * np.sqrt(n)) if n and sigma > 0 else np.nan), n
