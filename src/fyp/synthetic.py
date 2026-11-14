"""Synthetic counters with known answers, for testing the pipeline before real data.

`simulate_counter` plants a drifting sensitivity, an asymmetric response, a one-day lag
from mismatched closing times, fat tails and days without trades. `ic_power` runs the
monthly information-coefficient test the plan uses, under a planted signal or none.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def _t_noise(rng, n, scale, df=4):
    return rng.standard_t(df, n) * scale / np.sqrt(df / (df - 2))


def simulate_counter(T: int = 2500, seed: int = 0, beta0: float = 1.0, q: float = 4e-5,
                     sigma_c: float = 0.02, sigma_m: float = 0.01, sigma_e: float = 0.02,
                     gamma: float = 0.8, lag_share: float = 0.4, down_extra: float = 0.3,
                     p_notrade: float = 0.15) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=T)
    c = _t_noise(rng, T, sigma_c)
    m = _t_noise(rng, T, sigma_m)
    beta = beta0 + np.cumsum(rng.normal(0.0, np.sqrt(q), T))
    c_eff = np.where(c < 0, (1 + down_extra) * c, c)        # falls transmit more strongly
    c_eff_lag = np.r_[0.0, c_eff[:-1]]
    r_true = beta * ((1 - lag_share) * c_eff + lag_share * c_eff_lag) + gamma * m + _t_noise(rng, T, sigma_e)

    traded = rng.random(T) > p_notrade                       # thin trading
    observed = np.zeros(T)
    pending = 0.0
    for t in range(T):
        pending += r_true[t]
        if traded[t]:
            observed[t], pending = pending, 0.0
    return pd.DataFrame({"r": observed, "c": c, "m": m, "beta_true": beta, "traded": traded}, index=dates)


def ic_power(n_names: int, n_months: int, ic: float, n_sims: int = 4000, alpha: float = 0.05,
             seed: int = 0) -> float:
    """Share of simulated studies in which a t-test on the mean monthly Spearman IC rejects zero."""
    rng = np.random.default_rng(seed)
    rho = 2 * np.sin(np.pi * ic / 6)                         # Pearson rho giving this Spearman IC
    rejections = 0
    for _ in range(n_sims):
        s = rng.standard_normal((n_months, n_names))
        r = rho * s + np.sqrt(1 - rho ** 2) * rng.standard_normal((n_months, n_names))
        rs = np.argsort(np.argsort(s, axis=1), axis=1).astype(float)
        rr = np.argsort(np.argsort(r, axis=1), axis=1).astype(float)
        rs -= rs.mean(axis=1, keepdims=True); rr -= rr.mean(axis=1, keepdims=True)
        ics = (rs * rr).sum(axis=1) / np.sqrt((rs ** 2).sum(axis=1) * (rr ** 2).sum(axis=1))
        t = ics.mean() / (ics.std(ddof=1) / np.sqrt(n_months))
        if 2 * stats.t.sf(abs(t), n_months - 1) < alpha:
            rejections += 1
    return rejections / n_sims
