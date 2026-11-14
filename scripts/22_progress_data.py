"""Counts and ranges for the interim progress deck, computed from the pipeline's own tables.

Output: interim/progress_data.json  (the deck also reads consultation/deck_data.json for chart series)
Run:  .venv/bin/python -I scripts/22_progress_data.py
"""
from __future__ import annotations

import json

import pandas as pd

from fyp import config

out_dir = config.ROOT / "interim"
out_dir.mkdir(exist_ok=True)

log = pd.read_csv(config.REFERENCE / "collection_log.csv")
series = pd.read_csv(config.REFERENCE / "series.csv")
lc = pd.read_csv(config.TABLES / "liquidity_costs.csv")
filt = pd.read_csv(config.TABLES / "turnover_filter.csv").set_index("threshold_sgd")
daily = pd.read_parquet(config.PROCESSED / "series_daily.parquet")
sti = daily["sti"].dropna()

core = lc[(lc["group"] == "core") & (lc["status"] == "trading")]
rt = core.sort_values("round_trip_floor_pct")

data = dict(
    equities_in_universe=int(len(config.UNIVERSE)),
    equities_downloaded=int(((log["kind"] == "equity") & (log["status"] == "ok")).sum()),
    series_total=int(len(series)),
    series_yahoo=int((series["source"] == "yahoo").sum()),
    series_fred=int((series["source"] == "fred").sum()),
    sgx_snapshot_securities=int(log.loc[log["kind"] == "snapshot", "rows"].iloc[0]),
    first_date=str(sti.index.min().date()),
    last_date=str(sti.index.max().date()),
    sgx_trading_days=int(len(sti)),
    core_in_universe=int(len(config.CORE)),
    core_trading=int(len(core)),
    pass_100k=int(filt.loc[100000, "counters_passing"]),
    pass_1m=int(filt.loc[1000000, "counters_passing"]),
    round_trip_min=round(float(rt["round_trip_floor_pct"].iloc[0]), 2),
    round_trip_min_name=str(rt["name"].iloc[0]),
    round_trip_max=round(float(rt["round_trip_floor_pct"].iloc[-1]), 2),
    round_trip_max_name=str(rt["name"].iloc[-1]),
    scripts=sorted(p.name for p in (config.ROOT / "scripts").glob("[0-9]*.py")),
)
(out_dir / "progress_data.json").write_text(json.dumps(data, indent=1))
print(json.dumps({k: v for k, v in data.items() if k != "scripts"}, indent=1))
