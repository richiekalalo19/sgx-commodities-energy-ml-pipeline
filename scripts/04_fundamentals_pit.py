"""Point-in-time fundamentals panel, version 0, from free annual statements (plan task 5, Aim 2 inputs).

Source: Yahoo Finance annual income statement, balance sheet and cash flow for each core counter,
FY2021 or FY2022 to FY2025 (the "5 years of fundamentals" the submitted plan asks for). Raw statements
are written to data/raw/yahoo_fundamentals/<date>/ and never edited; --offline rebuilds from the latest.

Point-in-time rule: SGX's announcement API is closed, so filing timestamps are not available. A fiscal
year's figures become usable 60 days after the fiscal year end, the SGX deadline for full-year results
(Mainboard Rule 705; verify). A 120-day version (annual report and AGM window) is kept as a robustness
column. Valuation ratios use the unadjusted SGX close on each day and the latest usable statement.

Known limits, stated in the report:
  * Yahoo shows the latest, possibly restated, figures, not the figures as first reported.
  * No hedge ratios or cost-position disclosures (hand collection from annual reports, plan task 6).
    The EBITDA-margin gap to the segment median is only a crude cost-position proxy.
  * The Piotroski F-score needs a prior year, so it starts one year after a counter's first statement.

Outputs: data/processed/fundamentals_annual.parquet  (one row per counter and fiscal year)
         data/processed/fundamentals_daily.parquet   (SGX calendar, point-in-time, with daily valuation)
         reports/tables/fundamentals_coverage_pit.csv
Run:  .venv/bin/python -I scripts/04_fundamentals_pit.py [--offline]
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from datetime import date

import numpy as np
import pandas as pd

from fyp import config
from fyp.panel import load

warnings.filterwarnings("ignore")

LAG_DAYS, LAG_DAYS_SLOW = 60, 120
# Yahoo labels Mermaid Maritime's statements THB, but their size (FY2025 revenue 489m, total assets 450m)
# only makes sense in US dollars; in baht the group would be a tenth of its fleet's value. Checked 2026-11-10.
CURRENCY_OVERRIDE = {"DU4": "USD"}
RAW_ROOT = config.RAW / "yahoo_fundamentals"


# ---------------------------------------------------------------- collection
def download(folder):
    import yfinance as yf
    folder.mkdir(parents=True, exist_ok=True)
    meta = {}
    for c in config.CORE:
        t = yf.Ticker(c.yahoo)
        try:
            t.income_stmt.to_csv(folder / f"{c.code}_income.csv")
            t.balance_sheet.to_csv(folder / f"{c.code}_balance.csv")
            t.cashflow.to_csv(folder / f"{c.code}_cashflow.csv")
            info = t.info
            meta[c.code] = dict(financial_currency=info.get("financialCurrency"), quote_currency=info.get("currency"))
        except Exception as e:  # keep going; the coverage table shows the gap
            meta[c.code] = dict(error=str(e)[:120])
        time.sleep(0.6)
    # Thai baht per US dollar, for Mermaid Maritime's THB statements (kept here, not in the main panel)
    thb = yf.Ticker("THB=X").history(start="2013-01-01")["Close"]
    thb.index = thb.index.tz_localize(None)
    thb.rename("thb_per_usd").to_csv(folder / "fx_THB.csv")
    (folder / "meta.json").write_text(json.dumps(meta, indent=1))


if "--offline" in sys.argv:
    folder = sorted(p for p in RAW_ROOT.iterdir() if p.is_dir())[-1]
else:
    folder = RAW_ROOT / date.today().isoformat()
    download(folder)
meta = json.loads((folder / "meta.json").read_text())
print(f"Statements from {folder}")


def statement(code, kind):
    p = folder / f"{code}_{kind}.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, index_col=0)
    df.columns = pd.to_datetime(df.columns)
    return df


def pick(df, *names):
    for n in names:
        if n in df.index:
            return df.loc[n]
    return pd.Series(np.nan, index=df.columns)


# ---------------------------------------------------------------- annual features
seg = {c.code: c.segment for c in config.CORE}
rows = []
for c in config.CORE:
    inc, bs, cf = statement(c.code, "income"), statement(c.code, "balance"), statement(c.code, "cashflow")
    if inc.empty or bs.empty:
        continue
    years = sorted(set(inc.columns) & set(bs.columns))
    f = pd.DataFrame(index=years)
    f["revenue"] = pick(inc, "Total Revenue", "Operating Revenue")
    f["cost_of_revenue"] = pick(inc, "Cost Of Revenue", "Reconciled Cost Of Revenue")
    f["gross_profit"] = pick(inc, "Gross Profit")
    f["gross_profit"] = f["gross_profit"].fillna(f["revenue"] - f["cost_of_revenue"])
    f["ebitda"] = pick(inc, "EBITDA", "Normalized EBITDA")
    f["net_income"] = pick(inc, "Net Income Common Stockholders", "Net Income")
    f["total_assets"] = pick(bs, "Total Assets")
    f["total_debt"] = pick(bs, "Total Debt")
    f["cash"] = pick(bs, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
    f["net_debt"] = pick(bs, "Net Debt")
    f["net_debt"] = f["net_debt"].fillna(f["total_debt"] - f["cash"])
    f["equity"] = pick(bs, "Stockholders Equity", "Common Stock Equity")
    f["current_assets"] = pick(bs, "Current Assets")
    f["current_liabilities"] = pick(bs, "Current Liabilities")
    f["shares"] = pick(bs, "Ordinary Shares Number", "Share Issued")
    f["cfo"] = pick(cf, "Operating Cash Flow") if not cf.empty else np.nan
    f["capex"] = -pick(cf, "Capital Expenditure") if not cf.empty else np.nan   # positive = spending

    f["net_debt_ebitda"] = np.where(f["ebitda"] > 0, f["net_debt"] / f["ebitda"], np.nan)
    f["capex_intensity"] = f["capex"] / f["revenue"]
    f["cfo_to_net_income"] = np.where(f["net_income"] > 0, f["cfo"] / f["net_income"], np.nan)
    f["ebitda_margin"] = f["ebitda"] / f["revenue"]
    f["gross_margin"] = f["gross_profit"] / f["revenue"]
    f["debt_to_assets"] = f["total_debt"] / f["total_assets"]
    f["current_ratio"] = f["current_assets"] / f["current_liabilities"]

    # Piotroski (2000) F-score: nine binary signals, each needing the prior fiscal year
    prev = f.shift(1)
    roa = f["net_income"] / prev["total_assets"]
    roa_prev = prev["net_income"] / prev["total_assets"].shift(1)
    signals = pd.DataFrame({
        "f_roa": roa > 0,
        "f_cfo": f["cfo"] > 0,
        "f_droa": roa > roa_prev,
        "f_accrual": (f["cfo"] / prev["total_assets"]) > roa,
        "f_dlever": f["debt_to_assets"] < prev["debt_to_assets"],
        "f_dliquid": f["current_ratio"] > prev["current_ratio"],
        "f_noissue": f["shares"] <= prev["shares"],
        "f_dmargin": f["gross_margin"] > prev["gross_margin"],
        "f_dturn": (f["revenue"] / prev["total_assets"]) > (prev["revenue"] / prev["total_assets"].shift(1)),
    })
    inputs = pd.DataFrame({
        "f_roa": roa, "f_cfo": f["cfo"], "f_droa": roa_prev, "f_accrual": f["cfo"] / prev["total_assets"],
        "f_dlever": prev["debt_to_assets"], "f_dliquid": prev["current_ratio"], "f_noissue": prev["shares"],
        "f_dmargin": prev["gross_margin"], "f_dturn": prev["revenue"] / prev["total_assets"].shift(1)})
    signals = signals.where(inputs.notna())
    f["fscore_n"] = signals.notna().sum(axis=1)
    f["fscore"] = np.where(f["fscore_n"] == 9, signals.sum(axis=1, min_count=9), np.nan)
    f["roa"] = roa

    f["code"], f["name"], f["segment"] = c.code, c.name, c.segment
    f["financial_currency"] = CURRENCY_OVERRIDE.get(c.code, meta.get(c.code, {}).get("financial_currency"))
    f["fiscal_year_end"] = f.index
    f["available"] = f.index + pd.Timedelta(days=LAG_DAYS)
    f["available_slow"] = f.index + pd.Timedelta(days=LAG_DAYS_SLOW)
    rows.append(f.reset_index(drop=True))

annual = pd.concat(rows, ignore_index=True)
# Yahoo sometimes returns an empty oldest column; drop fiscal years with no income or balance-sheet data
annual = annual.dropna(subset=["revenue", "net_income", "total_assets"], how="all").reset_index(drop=True)
# Crude cost-position proxy: EBITDA margin minus the segment median in the same fiscal year
annual["fy"] = annual["fiscal_year_end"].dt.year
annual["ebitda_margin_gap"] = annual["ebitda_margin"] - annual.groupby(["segment", "fy"])["ebitda_margin"].transform("median")
annual["fscore_segment_pct"] = annual.groupby(["segment", "fy"])["fscore"].rank(pct=True)

# ---------------------------------------------------------------- daily point-in-time panel
close = load("equity_close")          # unadjusted SGX close, for market value
daily = load("series_daily")
sgx = daily["sti"].dropna().index
sgx = sgx[sgx >= annual["available"].min()]
usdsgd = daily["usdsgd"].reindex(sgx).ffill()           # SGD per USD
fx_per_usd = {"USD": pd.Series(1.0, index=sgx), "SGD": usdsgd,
              "IDR": daily["usdidr"].reindex(sgx).ffill(), "MYR": daily["usdmyr"].reindex(sgx).ffill()}
if (folder / "fx_THB.csv").exists():
    thb = pd.read_csv(folder / "fx_THB.csv", index_col=0, parse_dates=True).iloc[:, 0].sort_index()
    fx_per_usd["THB"] = thb.reindex(sgx, method="ffill")

keep = ["code", "fiscal_year_end", "net_debt_ebitda", "capex_intensity", "cfo_to_net_income", "ebitda_margin",
        "ebitda_margin_gap", "gross_margin", "debt_to_assets", "current_ratio", "roa", "fscore", "fscore_n",
        "fscore_segment_pct", "net_income", "ebitda", "net_debt", "equity", "shares", "financial_currency"]
parts = []
for code, g in annual.groupby("code"):
    g = g.sort_values("available").copy()
    # Move each availability date to the first SGX trading day on or after it (it can fall on a weekend)
    pos = sgx.searchsorted(g["available"].values)
    g = g[pos < len(sgx)]
    g["available_from"] = sgx[pos[pos < len(sgx)]]
    d = pd.DataFrame(index=sgx)
    d = d.join(g.set_index("available_from")[keep], how="left").ffill()
    d["available_from"] = pd.Series(g["available_from"].values, index=g["available_from"].values).reindex(sgx, method="ffill")
    d = d[d["code"].notna()]
    if code in close:
        px = close[code].reindex(d.index).ffill()
        cur = d["financial_currency"].iloc[-1]
        if cur in fx_per_usd:
            # market value in the statement currency: SGD -> USD -> statement currency
            mv = px * d["shares"] / usdsgd.reindex(d.index) * fx_per_usd[cur].reindex(d.index)
            d["pe"] = np.where(d["net_income"] > 0, mv / d["net_income"], np.nan)
            d["ev_ebitda"] = np.where(d["ebitda"] > 0, (mv + d["net_debt"]) / d["ebitda"], np.nan)
            d["pb"] = np.where(d["equity"] > 0, mv / d["equity"], np.nan)
    d["code"] = code
    parts.append(d)
pit = pd.concat(parts).rename_axis("date").reset_index()

config.PROCESSED.mkdir(parents=True, exist_ok=True)
annual.to_parquet(config.PROCESSED / "fundamentals_annual.parquet", index=False)
pit.to_parquet(config.PROCESSED / "fundamentals_daily.parquet", index=False)

cov = annual.groupby(["code", "name"]).agg(
    fiscal_years=("fy", "count"), first_fy=("fy", "min"), last_fy=("fy", "max"),
    currency=("financial_currency", "first"),
    net_debt_ebitda=("net_debt_ebitda", "count"), cfo_to_ni=("cfo_to_net_income", "count"),
    capex_intensity=("capex_intensity", "count"), fscore=("fscore", "count")).reset_index()
last = pit.sort_values("date").groupby("code").tail(1).set_index("code")
cov["pe_latest"] = cov["code"].map(last["pe"]) if "pe" in last else np.nan
cov["ev_ebitda_latest"] = cov["code"].map(last["ev_ebitda"]) if "ev_ebitda" in last else np.nan
cov.to_csv(config.TABLES / "fundamentals_coverage_pit.csv", index=False)

pd.set_option("display.width", 220)
print(f"\n{annual['code'].nunique()} counters, {len(annual)} counter-years; daily panel {len(pit):,} rows, "
      f"{pit['date'].min().date()} to {pit['date'].max().date()}; usable {LAG_DAYS} days after fiscal year end")
print(cov.round(2).to_string(index=False))
