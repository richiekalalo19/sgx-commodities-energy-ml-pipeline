"""Builds data/processed/*.parquet from the latest raw downloads and prints quality checks.

Run:  .venv/bin/python -I scripts/02_build_panel.py
"""
from __future__ import annotations

import pandas as pd

from fyp import config
from fyp.panel import build_and_save

out = build_and_save()
eq, daily, monthly = out["equity"], out["daily"], out["monthly"]

close, vol = eq["close"], eq["volume"]
rows = []
for code in close.columns:
    p = close[code].dropna()
    v = vol[code].reindex(p.index)
    since = p.index >= "2014-01-01"
    rows.append(dict(
        code=code,
        first=p.index.min().date(), last=p.index.max().date(), days=len(p),
        zero_volume_pct=round(100 * (v[since].fillna(0) == 0).mean(), 1),
        unchanged_close_pct=round(100 * (p[since].diff() == 0).mean(), 1),
        last_close=p.iloc[-1],
    ))
q = pd.DataFrame(rows)
config.TABLES.mkdir(parents=True, exist_ok=True)
q.to_csv(config.TABLES / "equity_quality.csv", index=False)
print(q.to_string(index=False))

print("\nDaily series coverage")
print(daily.apply(lambda s: pd.Series({"first": s.first_valid_index().date(), "last": s.last_valid_index().date(),
                                       "obs": s.notna().sum()})).T.to_string())
print("\nMonthly series coverage")
print(monthly.apply(lambda s: pd.Series({"first": s.first_valid_index().date(), "last": s.last_valid_index().date(),
                                         "obs": s.notna().sum()})).T.to_string())

# Is CPO=F palm oil in USD/tonne? Compare with the IMF monthly palm-oil price.
cpo_m = daily["palm"].resample("MS").mean()
both = pd.concat([cpo_m.rename("CPO=F monthly mean"), monthly["palm_m"].rename("IMF PPOILUSDM")], axis=1).dropna()
print("\nCPO=F against IMF palm oil (USD/tonne)")
print(both.loc["2021-10":"2022-08"].round(0).to_string())
print("correlation of monthly levels:", round(both.corr().iloc[0, 1], 3))
r = both.pct_change().dropna()
print("correlation of monthly changes:", round(r.corr().iloc[0, 1], 3))
stale = (daily["palm"].dropna().diff() == 0).mean()
print(f"CPO=F share of unchanged daily closes: {stale:.1%}")
