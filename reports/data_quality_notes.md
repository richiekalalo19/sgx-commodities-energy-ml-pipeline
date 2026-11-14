# Data quality notes

Findings from the first collection run on 21 October 2026. Each one changes how a series can be used.

## 1. CPO=F is not a daily palm-oil price

Yahoo's `CPO=F` is CME's USD Malaysian Crude Palm Oil **calendar** future, settled on the monthly average of
Bursa FCPO settlement prices. The rows are settlement-only (open = high = low = close, almost always zero volume).

Evidence:

- Its monthly average tracks the IMF palm-oil price closely (correlation 0.99 in levels, 0.91 in monthly changes),
  so the level is right.
- Its daily moves are 3.9 times larger on the first trading day of a month than on other days (contract roll), and
  moves in the last five days of a month are 0.27 times those in the first five (the month's average is mostly fixed).
  Brent and gold futures show neither pattern (1.3 and 0.8 to 0.9).
- On 25 April 2022, the first session after Indonesia announced its export ban, it fell 0.7%. On 2 May it jumped 8.5%
  when the May contract became the front month.

Consequence: daily palm betas from `CPO=F` are biased toward zero and its daily timing is unusable for event studies.
The daily palm results in `reports/tables/passthrough_daily.csv` are flagged. Use Bloomberg FCPO (generic third
month, which is what the CME contract settles against) or monthly data.

## 2. Continuous futures series roll

`BZ=F`, `GC=F` and `MTF=F` are front-month continuous series without back-adjustment. Roll days carry a small
artificial return. Using FRED Brent spot instead of `BZ=F` lowers Dimson betas by 20 to 35% but leaves the next-day
share broadly unchanged (`passthrough_brent_spot_check.csv`). Back-adjust or use spot before the harness is frozen.
`MTF=F` (API2 Rotterdam coal) also stops on 26 December 2025.

## 3. Price index versus total return

Yahoo's `^STI` is a price index. The STI total-return benchmark is the SPDR STI ETF (`ES3.SI`) adjusted close:
8.4% a year since 2014 against 4.5% for the price index. Comparing total-return portfolios with `^STI` would flatter
them by about 4% a year. Equity adjusted closes on Yahoo do include dividends (checked against close plus dividends).

## 4. Counters missing or inactive

- **Golden Energy and Resources (AUE)**, delisted 28 September 2023, is not on Yahoo. Its history is needed to avoid
  survivorship bias; get it from Bloomberg.
- **Interra Resources (5GI)** has not traded since 31 January 2025 (Yahoo carries flat zero-volume rows after that).
  Confirm whether it is suspended.
- **Kencana Agri (BNE)** trades on about 80% of days and has a median daily value near S$10k.

## 5. Tick discreteness

Closing prices are unchanged from the previous day on 30 to 38% of days for Golden Agri, Marco Polo Marine,
IndoAgri and Union Gas, because one tick is larger than a typical daily move. Daily regressions on these counters
are attenuated. This supports weekly and monthly horizons.

## 6. Fundamentals and announcements

- yfinance gives 4 to 5 annual statements (FY2021 to FY2025) per counter and almost no quarterly data. The 2014 to
  2020 part of the fundamental panel needs Bloomberg, the SGX screener or annual reports.
- The SGX announcements API returns 403 or 401 without a session, so results-announcement timestamps must come from
  Bloomberg, Factiva or manual collection.
- FRED has no Singapore short rate. Sharpe ratios and alphas currently use a zero risk-free rate; add SORA or the
  3-month SGS T-bill from MAS.

## 7. Calendars

Each market keeps its own calendar. IDX was closed for the long Lebaran holiday from 29 April to 6 May 2022, during
the export ban, so IDX abnormal returns over that window come from fewer sessions.
