"""Builds the processed panel: wide daily tables per field, plus daily and monthly series.

Equities keep their own exchange calendars (SGX, Bursa, IDX). Returns are computed on each
instrument's own trading days before any alignment, so a holiday never fakes a zero return.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .data_sources import latest_raw_dir, safe_name

FIELDS = {"open": "Open", "high": "High", "low": "Low", "close": "Close",
          "adjclose": "Adj Close", "volume": "Volume", "dividends": "Dividends"}


def load_yahoo(symbol: str) -> pd.DataFrame:
    path = latest_raw_dir("yahoo") / f"{safe_name(symbol)}.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def load_fred(series_id: str) -> pd.Series:
    path = latest_raw_dir("fred") / f"{series_id}.csv"
    if not path.exists():
        return pd.Series(dtype=float, name=series_id)
    df = pd.read_csv(path)
    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = pd.to_datetime(df[df.columns[0]])
    s.index.name = "date"
    return s.dropna().rename(series_id)


def clean_equity(df: pd.DataFrame) -> pd.DataFrame:
    """Drops rows with no price and rows Yahoo fills on exchange holidays."""
    if df.empty:
        return df
    df = df[df["Close"].notna() & (df["Close"] > 0)].copy()
    # Yahoo sometimes carries a holiday row with zero volume and an unchanged OHLC bar.
    flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
    holiday = flat & (df["Volume"].fillna(0) == 0) & (df["Close"] == df["Close"].shift(1))
    return df[~holiday]


def equity_tables() -> dict[str, pd.DataFrame]:
    frames = {k: {} for k in FIELDS}
    for c in config.UNIVERSE:
        df = clean_equity(load_yahoo(c.yahoo))
        if df.empty:
            continue
        for k, col in FIELDS.items():
            frames[k][c.code] = df[col] if col in df else pd.Series(index=df.index, dtype=float)
    return {k: pd.DataFrame(v).sort_index() for k, v in frames.items()}


def series_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    daily, monthly = {}, {}
    for s in config.SERIES:
        if s.source == "yahoo":
            df = load_yahoo(s.symbol)
            if df.empty:
                continue
            # Adjusted close carries dividends for the ETF benchmark; it equals Close for futures, FX and indices.
            col = "Adj Close" if "Adj Close" in df else "Close"
            ser = df[col].where(df[col] > 0)
        else:
            ser = load_fred(s.symbol)
        if ser.empty:
            continue
        (daily if s.frequency == "daily" else monthly)[s.key] = ser
    return pd.DataFrame(daily).sort_index(), pd.DataFrame(monthly).sort_index()


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Per-column log returns on each column's own observed days."""
    out = {}
    for col in prices:
        p = prices[col].dropna()
        out[col] = np.log(p).diff()
    return pd.DataFrame(out)


def build_and_save() -> dict:
    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    eq = equity_tables()
    for k, df in eq.items():
        df.to_parquet(config.PROCESSED / f"equity_{k}.parquet")
    daily, monthly = series_tables()
    daily.to_parquet(config.PROCESSED / "series_daily.parquet")
    monthly.to_parquet(config.PROCESSED / "series_monthly.parquet")
    return {"equity": eq, "daily": daily, "monthly": monthly}


def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(config.PROCESSED / f"{name}.parquet")
