"""Pass-through estimators: same-day OLS, Dimson lead-and-lag, asymmetric, rolling.

All regressions use Newey-West (HAC) standard errors. Factor returns are put on the
equity's exchange calendar first (see `on_calendar`), so a factor that settles after the
SGX close shows up as a lag, which is exactly what the Dimson terms are there to absorb.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


def on_calendar(prices: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """Log returns of a price series sampled on `dates` (last available value carried forward)."""
    p = prices.dropna()
    p = p.reindex(p.index.union(dates)).ffill().reindex(dates)
    return np.log(p).diff()


def equity_on_calendar(prices: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """Equity log returns on `dates`, limited to the counter's trading life (no returns after suspension)."""
    p = prices.dropna()
    if p.empty:
        return pd.Series(index=dates, dtype=float)
    d = dates[(dates >= p.index.min()) & (dates <= p.index.max())]
    return on_calendar(p, d).reindex(dates)


def ols(y: pd.Series, X: pd.DataFrame, hac_lags: int = 5):
    data = pd.concat([y.rename("y"), X], axis=1).dropna()
    model = sm.OLS(data["y"], sm.add_constant(data.drop(columns="y"), has_constant="add"))
    return model.fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})


class Contrast:
    """Linear combination of coefficients with its (HAC) standard error, t-statistic and p-value."""

    def __init__(self, fit, weights: dict[str, float]):
        w = np.array([weights.get(name, 0.0) for name in fit.params.index])
        cov = np.asarray(fit.cov_params())
        self.effect = float(w @ fit.params.values)
        self.se = float(np.sqrt(w @ cov @ w))
        self.tvalue = self.effect / self.se if self.se > 0 else np.nan
        self.pvalue = float(2 * stats.norm.sf(abs(self.tvalue)))


def contrast(fit, weights: dict[str, float]) -> Contrast:
    return Contrast(fit, weights)


def shifted(s: pd.Series, name: str, lags=(1, 0, -1)) -> pd.DataFrame:
    """Columns name_lag1 (t-1), name_0 (t), name_lead1 (t+1)."""
    cols = {}
    for k in lags:
        label = f"{name}_0" if k == 0 else (f"{name}_lag{k}" if k > 0 else f"{name}_lead{-k}")
        cols[label] = s.shift(k)
    return pd.DataFrame(cols)


def dimson(r: pd.Series, c: pd.Series, m: pd.Series, x: pd.Series | None = None) -> dict:
    """Same-day against Dimson (one lag, one lead) commodity sensitivity, with R-squared steps."""
    parts = [r.rename("r"), shifted(c, "c"), shifted(m, "m")]
    controls = ["m_0"]
    if x is not None:
        parts.append(x.rename("x_0"))
        controls.append("x_0")
    sample = pd.concat(parts, axis=1).dropna()
    y = sample["r"]

    fit_m = ols(y, sample[controls])
    fit_same = ols(y, sample[["c_0"] + controls])
    dim_cols = ["c_lag1", "c_0", "c_lead1", "m_lag1", "m_0", "m_lead1"] + (["x_0"] if x is not None else [])
    fit_dim = ols(y, sample[dim_cols])

    sum_test = contrast(fit_dim, {"c_lag1": 1, "c_0": 1, "c_lead1": 1})
    return dict(
        n=int(fit_dim.nobs),
        r2_market=fit_m.rsquared,
        r2_same_day=fit_same.rsquared,
        r2_dimson=fit_dim.rsquared,
        beta_same_day=fit_same.params["c_0"],
        t_same_day=fit_same.tvalues["c_0"],
        beta_lag=fit_dim.params["c_lag1"],
        t_lag=fit_dim.tvalues["c_lag1"],
        beta_0=fit_dim.params["c_0"],
        beta_lead=fit_dim.params["c_lead1"],
        t_lead=fit_dim.tvalues["c_lead1"],
        beta_dimson=float(np.squeeze(sum_test.effect)),
        t_dimson=float(np.squeeze(sum_test.tvalue)),
    )


def weekly(r: pd.Series) -> pd.Series:
    """Weekly (Friday) log returns from daily log returns."""
    return r.resample("W-FRI").sum(min_count=1)


def asymmetric(r: pd.Series, c: pd.Series, m: pd.Series) -> dict:
    """Separate sensitivities to rising and falling commodity weeks, with a Wald test of equality."""
    rw, cw, mw = weekly(r), weekly(c), weekly(m)
    X = pd.DataFrame({"c_up": cw.clip(lower=0), "c_down": cw.clip(upper=0), "m": mw})
    fit = ols(rw, X, hac_lags=4)
    test = contrast(fit, {"c_up": 1, "c_down": -1})
    return dict(
        n_weeks=int(fit.nobs),
        beta_up=fit.params["c_up"], t_up=fit.tvalues["c_up"],
        beta_down=fit.params["c_down"], t_down=fit.tvalues["c_down"],
        diff=float(np.squeeze(test.effect)), t_diff=float(np.squeeze(test.tvalue)),
        p_diff=float(np.squeeze(test.pvalue)),
    )


def rolling_dimson(r: pd.Series, c: pd.Series, m: pd.Series, window: int = 252, step: int = 21) -> pd.Series:
    """Rolling Dimson sensitivity, re-estimated every `step` days on the trailing `window` days."""
    data = pd.concat([r.rename("r"), shifted(c, "c"), shifted(m, "m")], axis=1).dropna()
    out = {}
    for end in range(window, len(data) + 1, step):
        chunk = data.iloc[end - window:end]
        X = sm.add_constant(chunk.drop(columns="r"))
        b = np.linalg.lstsq(X.values, chunk["r"].values, rcond=None)[0]
        coef = dict(zip(X.columns, b))
        out[chunk.index[-1]] = coef["c_lag1"] + coef["c_0"] + coef["c_lead1"]
    return pd.Series(out, name="rolling_dimson")
