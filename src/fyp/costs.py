"""Trading-cost model: SGX tick schedule, fees, and spread and illiquidity estimates from daily bars."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def tick_size(price):
    """SGX minimum bid size for a stock at this price (vectorised)."""
    p = np.asarray(price, dtype=float)
    out = np.full(p.shape, np.nan)
    lower = 0.0
    for upper, tick in config.TICK_SCHEDULE:
        out[(p >= lower) & (p < upper)] = tick
        lower = upper
    return out


def fee_per_side(fees: dict = config.FEES) -> float:
    return (fees["clearing"] + fees["trading_access"] + fees["brokerage"]) * (1 + fees["gst"])


def round_trip_cost(price, spread_ticks: float = 1.0) -> np.ndarray:
    """Cost of buying and selling once, as a fraction of price: the spread crossed plus fees on both sides."""
    p = np.asarray(price, dtype=float)
    return spread_ticks * tick_size(p) / p + 2 * fee_per_side()


def corwin_schultz(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Corwin and Schultz (2012) high-low spread estimator, with the overnight-gap adjustment.

    Returns a daily series of two-day spread estimates (fractions of price); negative estimates are set to zero.
    """
    h, l = high.astype(float).copy(), low.astype(float).copy()
    prev_close = close.astype(float).shift(1)
    gap_up = (l - prev_close).clip(lower=0)
    gap_down = (h - prev_close).clip(upper=0)
    h, l = h - gap_up - gap_down, l - gap_up - gap_down
    with np.errstate(divide="ignore", invalid="ignore"):
        beta = np.log(h / l) ** 2 + np.log(h.shift(-1) / l.shift(-1)) ** 2
        gamma = np.log(np.maximum(h, h.shift(-1)) / np.minimum(l, l.shift(-1))) ** 2
        k = 3 - 2 * np.sqrt(2)
        alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
        spread = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    return spread.clip(lower=0)


def amihud(ret: pd.Series, traded_value: pd.Series) -> float:
    """Amihud (2002) illiquidity: mean absolute return per S$1 million traded."""
    x = (ret.abs() / traded_value.replace(0, np.nan)).dropna()
    return float(x.mean() * 1e6) if len(x) else np.nan
