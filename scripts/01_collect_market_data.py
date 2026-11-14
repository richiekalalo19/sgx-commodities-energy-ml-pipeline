"""Download every free series the plan needs and log what came back.

Writes raw files under data/raw/<source>/<date>/ and a collection log under data/reference/.
Run:  .venv/bin/python -I scripts/01_collect_market_data.py
"""
from __future__ import annotations

import time
import warnings

import pandas as pd

from fyp import config
from fyp.data_sources import (TODAY, fetch_fred, fetch_sgx_securities, fetch_yahoo, raw_dir,
                              safe_name, save_json)

warnings.filterwarnings("ignore")


def log_row(kind, key, source, symbol, df_or_s, status=""):
    if df_or_s is None or len(df_or_s) == 0:
        return dict(kind=kind, key=key, source=source, symbol=symbol, rows=0, first="", last="",
                    status=status or "empty")
    idx = df_or_s.index
    return dict(kind=kind, key=key, source=source, symbol=symbol, rows=len(df_or_s),
                first=idx.min().date().isoformat(), last=idx.max().date().isoformat(), status=status or "ok")


def main() -> None:
    log = []

    # 1. SGX securities snapshot (current board, used for prices and survivorship checks)
    try:
        snap = fetch_sgx_securities()
        save_json(snap, raw_dir("sgx") / "securities_snapshot.json")
        n = len(snap.get("data", {}).get("prices", [])) if isinstance(snap.get("data"), dict) else 0
        log.append(dict(kind="snapshot", key="sgx_securities", source="sgx", symbol="api.sgx.com/securities/v1.1",
                        rows=n, first=TODAY, last=TODAY, status="ok"))
    except Exception as e:
        log.append(dict(kind="snapshot", key="sgx_securities", source="sgx", symbol="api.sgx.com/securities/v1.1",
                        rows=0, first="", last="", status=f"error: {e}"[:120]))

    # 2. Equities
    ydir = raw_dir("yahoo")
    for c in config.UNIVERSE:
        h = fetch_yahoo(c.yahoo)
        if len(h):
            h.to_csv(ydir / f"{safe_name(c.yahoo)}.csv")
        log.append(log_row("equity", c.code, "yahoo", c.yahoo, h,
                           "" if len(h) else "not on Yahoo (delisted or unsupported)"))
        time.sleep(0.8)

    # 3. Indices, commodities, FX and rates
    fdir = raw_dir("fred")
    for s in config.SERIES:
        if s.source == "yahoo":
            h = fetch_yahoo(s.symbol)
            if len(h):
                h.to_csv(ydir / f"{safe_name(s.symbol)}.csv")
            log.append(log_row("series", s.key, "yahoo", s.symbol, h))
            time.sleep(0.8)
        else:
            try:
                ser, text = fetch_fred(s.symbol)
                (fdir / f"{s.symbol}.csv").write_text(text)
                log.append(log_row("series", s.key, "fred", s.symbol, ser))
            except Exception as e:
                log.append(dict(kind="series", key=s.key, source="fred", symbol=s.symbol, rows=0,
                                first="", last="", status=f"error: {e}"[:120]))

    config.REFERENCE.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(log)
    out.insert(0, "collected", TODAY)
    out.to_csv(config.REFERENCE / "collection_log.csv", index=False)

    pd.DataFrame([vars(c) for c in config.UNIVERSE]).to_csv(config.REFERENCE / "universe.csv", index=False)
    pd.DataFrame([vars(s) for s in config.SERIES]).to_csv(config.REFERENCE / "series.csv", index=False)

    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
