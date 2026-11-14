"""Minimum detectable information coefficient for the cross-sectional test."""
from __future__ import annotations

import numpy as np
from scipy import stats


def mde_ic(n_names: int, n_periods: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Smallest mean Spearman IC a two-sided test detects with the given power.

    Under the null a Spearman coefficient across n names has standard error 1/sqrt(n-1);
    averaging n_periods independent periods divides it by sqrt(n_periods).
    """
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(z / np.sqrt(n_names - 1) / np.sqrt(n_periods))
