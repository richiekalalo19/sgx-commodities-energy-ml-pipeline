"""Records how much fundamental history the free sources give, and whether SGX announcements are reachable.

Output: data/reference/fundamentals_coverage.csv
Run:  .venv/bin/python -I scripts/03_probe_fundamentals.py
"""
from __future__ import annotations

import time
import warnings

import pandas as pd
import requests
import yfinance as yf

from fyp import config

warnings.filterwarnings("ignore")

rows = []
for c in config.CORE:
    t = yf.Ticker(c.yahoo)
    try:
        fa, fq, bs, cf = t.financials, t.quarterly_financials, t.balance_sheet, t.cashflow
        rows.append(dict(code=c.code, name=c.name, annual_income_statements=fa.shape[1],
                         quarterly_income_statements=fq.shape[1], annual_balance_sheets=bs.shape[1],
                         annual_cash_flows=cf.shape[1],
                         first_fiscal_year_end=fa.columns.min().date() if fa.shape[1] else None,
                         last_fiscal_year_end=fa.columns.max().date() if fa.shape[1] else None))
    except Exception as e:
        rows.append(dict(code=c.code, name=c.name, error=str(e)[:80]))
    time.sleep(0.6)
cov = pd.DataFrame(rows)
cov.to_csv(config.REFERENCE / "fundamentals_coverage.csv", index=False)
print(cov.to_string(index=False))

r = requests.get("https://api.sgx.com/announcements/v1.1/?periodstart=20250501_160000&periodend=20250515_155959"
                 "&pagestart=0&pagesize=20", timeout=30,
                 headers={"User-Agent": "Mozilla/5.0", "Origin": "https://www.sgx.com", "Referer": "https://www.sgx.com/"})
print(f"\nSGX announcements API: HTTP {r.status_code}")
