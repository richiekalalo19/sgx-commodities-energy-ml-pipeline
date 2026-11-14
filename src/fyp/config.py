"""Project configuration: paths, universe, market series and cost assumptions.

Every script imports from here, so each parameter is defined once.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
REFERENCE = DATA / "reference"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
CONSULT = ROOT / "consultation"

# One year of warm-up before the 2014 start in plan v2.
START = "2013-01-01"


@dataclass(frozen=True)
class Counter:
    code: str            # exchange trading code
    yahoo: str           # Yahoo Finance symbol
    name: str
    segment: str
    underlying: str      # key into SERIES, or "" when no clean underlying exists
    group: str = "core"  # core | delisted | levy-exposed | levy-comparison
    exchange: str = "SGX"
    note: str = ""


# The ~18-counter universe of plan v2, section 4, plus the delisted counter and the
# extra names the export-levy experiment needs (section 6.5).
UNIVERSE: list[Counter] = [
    # Agri-commodity and palm oil
    Counter("F34", "F34.SI", "Wilmar International", "Agri-commodity", "palm", note="Integrated processor and merchant; levy comparison"),
    Counter("E5H", "E5H.SI", "Golden Agri-Resources", "Agri-commodity", "palm", note="Indonesian grower; levy-exposed"),
    Counter("EB5", "EB5.SI", "First Resources", "Agri-commodity", "palm", note="Indonesian grower; levy-exposed"),
    Counter("P8Z", "P8Z.SI", "Bumitama Agri", "Agri-commodity", "palm", note="Indonesian grower; levy-exposed"),
    Counter("VC2", "VC2.SI", "Olam Group", "Agri-commodity", "", note="Diversified food ingredients; borderline"),
    # Oil and gas exploration
    Counter("5WH", "5WH.SI", "Rex International", "Oil & gas exploration", "brent"),
    Counter("T13", "T13.SI", "RH PetroGas", "Oil & gas exploration", "brent"),
    Counter("5GI", "5GI.SI", "Interra Resources", "Oil & gas exploration", "brent"),
    # Coal and mining
    Counter("RE4", "RE4.SI", "Geo Energy Resources", "Coal & mining", "coal"),
    Counter("5TP", "5TP.SI", "CNMC Goldmine", "Coal & mining", "gold"),
    # Energy infrastructure
    Counter("U96", "U96.SI", "Sembcorp Industries", "Energy infrastructure", "", note="Spark spread; no clean underlying"),
    Counter("BN4", "BN4.SI", "Keppel", "Energy infrastructure", "", note="2024 restructuring; borderline"),
    Counter("1F2", "1F2.SI", "Union Gas Holdings", "Energy infrastructure", "", note="Regulated LPG and gas retail"),
    # Energy services and offshore
    Counter("5E2", "5E2.SI", "Seatrium", "Energy services & offshore", "brent", note="Responds through customer capex"),
    Counter("5LY", "5LY.SI", "Marco Polo Marine", "Energy services & offshore", "brent"),
    Counter("DU4", "DU4.SI", "Mermaid Maritime", "Energy services & offshore", "brent"),
    # Fuel distribution and shipping
    Counter("G92", "G92.SI", "China Aviation Oil", "Fuel distribution & shipping", "jet"),
    Counter("S56", "S56.SI", "Samudera Shipping", "Fuel distribution & shipping", "", note="Container freight; crude is a cost"),
    # Delisted: kept to its delisting date to avoid survivorship bias
    Counter("AUE", "AUE.SI", "Golden Energy and Resources", "Coal & mining", "coal", group="delisted",
            note="Delisted 28 Sep 2023 after compulsory acquisition at S$0.181"),
    # Export-levy experiment: extra exposed growers listed on SGX and IDX
    Counter("5JS", "5JS.SI", "Indofood Agri Resources", "Agri-commodity", "palm", group="levy-exposed"),
    Counter("BNE", "BNE.SI", "Kencana Agri", "Agri-commodity", "palm", group="levy-exposed"),
    Counter("AALI", "AALI.JK", "Astra Agro Lestari", "Agri-commodity", "palm", group="levy-exposed", exchange="IDX"),
    Counter("LSIP", "LSIP.JK", "PP London Sumatra Indonesia", "Agri-commodity", "palm", group="levy-exposed", exchange="IDX"),
    Counter("SIMP", "SIMP.JK", "Salim Ivomas Pratama", "Agri-commodity", "palm", group="levy-exposed", exchange="IDX"),
    Counter("SSMS", "SSMS.JK", "Sawit Sumbermas Sarana", "Agri-commodity", "palm", group="levy-exposed", exchange="IDX"),
    # Export-levy experiment: Malaysian growers as the comparison group
    Counter("1961", "1961.KL", "IOI Corporation", "Agri-commodity", "palm", group="levy-comparison", exchange="Bursa"),
    Counter("2445", "2445.KL", "Kuala Lumpur Kepong", "Agri-commodity", "palm", group="levy-comparison", exchange="Bursa"),
    Counter("5285", "5285.KL", "SD Guthrie", "Agri-commodity", "palm", group="levy-comparison", exchange="Bursa"),
    Counter("2291", "2291.KL", "Genting Plantations", "Agri-commodity", "palm", group="levy-comparison", exchange="Bursa"),
]

CORE = [c for c in UNIVERSE if c.group == "core"]
INDONESIAN_GROWERS_SGX = ["E5H", "EB5", "P8Z", "5JS"]


@dataclass(frozen=True)
class Series:
    key: str
    source: str        # yahoo | fred
    symbol: str
    description: str
    frequency: str     # daily | monthly
    timing: str        # when the value becomes known, in Singapore time


SERIES: list[Series] = [
    # Equity indices
    Series("sti", "yahoo", "^STI", "Straits Times Index (price index, no dividends)", "daily", "17:00 SGT, same day"),
    Series("sti_etf", "yahoo", "ES3.SI", "SPDR STI ETF; adjusted close gives the STI total-return benchmark", "daily", "17:00 SGT, same day"),
    Series("klci", "yahoo", "^KLSE", "FTSE Bursa Malaysia KLCI", "daily", "17:00 MYT = 17:00 SGT, same day"),
    Series("jkse", "yahoo", "^JKSE", "Jakarta Composite Index", "daily", "16:00 WIB = 17:00 SGT, same day"),
    # Commodities, daily
    Series("palm", "yahoo", "CPO=F", "Crude palm oil, USD futures settled on Bursa FCPO (Yahoo CPO=F)", "daily", "Bursa FCPO day session ends 18:00 MYT, an hour after the SGX close"),
    Series("coal", "yahoo", "MTF=F", "Coal, API2 Rotterdam futures (Yahoo MTF=F; history ends Dec 2025)", "daily", "London close, after the SGX close"),
    Series("brent", "yahoo", "BZ=F", "Brent crude, ICE front-month futures", "daily", "settles 19:30 London, about 02:30 SGT next day"),
    Series("brent_spot", "fred", "DCOILBRENTEU", "Brent spot FOB Europe (EIA via FRED)", "daily", "London close, after the SGX close"),
    Series("wti", "yahoo", "CL=F", "WTI crude, NYMEX front-month futures", "daily", "settles 14:30 New York, about 02:30 SGT next day"),
    Series("gold", "yahoo", "GC=F", "Gold, COMEX front-month futures", "daily", "settles 13:30 New York, about 01:30 SGT next day"),
    Series("jet", "fred", "DJFUELUSGULF", "Jet fuel, US Gulf Coast spot (EIA via FRED)", "daily", "US close, after the SGX close"),
    Series("heating_oil", "yahoo", "HO=F", "NY Harbor ULSD futures (jet-fuel proxy)", "daily", "US close, after the SGX close"),
    Series("henry_hub", "yahoo", "NG=F", "Henry Hub natural gas futures", "daily", "US close, after the SGX close"),
    Series("dry_bulk", "yahoo", "BDRY", "Breakwave Dry Bulk Shipping ETF (freight futures proxy, from 2018)", "daily", "US close, after the SGX close"),
    # Commodities, monthly (fallback where no free daily series exists)
    Series("palm_m", "fred", "PPOILUSDM", "Global price of palm oil, monthly (IMF via FRED)", "monthly", "monthly average"),
    Series("coal_m", "fred", "PCOALAUUSDM", "Australian thermal coal, monthly (IMF via FRED)", "monthly", "monthly average"),
    Series("brent_m", "fred", "POILBREUSDM", "Brent crude, monthly (IMF via FRED)", "monthly", "monthly average"),
    Series("lng_m", "fred", "PNGASJPUSDM", "LNG, Japan, monthly (IMF via FRED)", "monthly", "monthly average"),
    # FX and risk
    Series("usdsgd", "yahoo", "SGD=X", "USD/SGD", "daily", "rolling 24 h; Yahoo close is London evening"),
    Series("usdmyr", "yahoo", "MYR=X", "USD/MYR", "daily", "rolling 24 h"),
    Series("usdidr", "yahoo", "IDR=X", "USD/IDR", "daily", "rolling 24 h"),
    Series("usdsgd_fred", "fred", "DEXSIUS", "SGD per USD, noon New York (FRED)", "daily", "noon New York = 00:00 SGT next day"),
    Series("vix", "fred", "VIXCLS", "CBOE VIX close (FRED)", "daily", "US close, after the SGX close"),
    # To do: a Singapore risk-free rate (SORA or 3-month SGS T-bill) from MAS; FRED has none.
]

# SGX minimum bid sizes for stocks (SGX Rulebook): S$0.001 below S$0.20,
# S$0.005 from S$0.20 to S$0.995, S$0.01 from S$1.00.
TICK_SCHEDULE = [(0.20, 0.001), (1.00, 0.005), (float("inf"), 0.01)]

# Per-side fee assumptions, as fractions of trade value. Verify against the current
# SGX fee schedule and a named broker before the cost model is frozen.
FEES = {
    "clearing": 0.000325,       # SGX clearing fee 0.0325%
    "trading_access": 0.000075, # SGX trading access fee 0.0075%
    "brokerage": 0.0008,        # representative online retail tier, 0.08%
    "gst": 0.09,                # GST on all three
}
