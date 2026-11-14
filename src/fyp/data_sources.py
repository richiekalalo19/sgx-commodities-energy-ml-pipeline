"""Downloaders for the free sources: Yahoo Finance, FRED and the open SGX securities endpoint.

Raw downloads are written once to data/raw/<source>/<YYYY-MM-DD>/ and never overwritten,
so every processed table can be traced to the file it came from.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

from . import config

TODAY = dt.date.today().isoformat()
HEADERS = {"User-Agent": "Mozilla/5.0 (A1088-261 research pipeline)"}


def raw_dir(source: str, stamp: str = TODAY) -> Path:
    d = config.RAW / source / stamp
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_raw_dir(source: str) -> Path:
    stamps = sorted(p for p in (config.RAW / source).iterdir() if p.is_dir())
    if not stamps:
        raise FileNotFoundError(f"no raw downloads for {source}; run scripts/01_collect_market_data.py")
    return stamps[-1]


def safe_name(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", symbol)


def fetch_yahoo(symbol: str, start: str = config.START, retries: int = 3) -> pd.DataFrame:
    """Daily OHLCV with dividends and splits, indexed by the exchange's local date."""
    import yfinance as yf

    for attempt in range(retries):
        try:
            h = yf.Ticker(symbol).history(start=start, auto_adjust=False, actions=True)
        except Exception:
            time.sleep(2 * (attempt + 1))
            continue
        if h.empty or not isinstance(h.index, pd.DatetimeIndex):
            return pd.DataFrame()
        if h.index.tz is not None:
            h.index = h.index.tz_localize(None)
        h.index = h.index.normalize()
        h.index.name = "date"
        return h
    return pd.DataFrame()


def fetch_fred(series_id: str) -> tuple[pd.Series, str]:
    """Returns the parsed series and the raw CSV text."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=60, headers=HEADERS)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = pd.to_datetime(df[df.columns[0]])
    s.index.name = "date"
    s.name = series_id
    return s.dropna(), r.text


def fetch_sgx_securities() -> dict:
    """Snapshot of every SGX security with its latest quote (open endpoint, no login)."""
    r = requests.get(
        "https://api.sgx.com/securities/v1.1",
        timeout=60,
        headers={**HEADERS, "Origin": "https://www.sgx.com", "Referer": "https://www.sgx.com/"},
    )
    r.raise_for_status()
    return r.json()


def save_json(obj: dict, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
