"""Builds consultation/brief.html: the decision brief as a web page, with every figure embedded in light and
dark versions and a table of the numbers under each figure.

Run:  .venv/bin/python -I scripts/21_brief_html.py
"""
from __future__ import annotations

import base64
import html
import io
import json

import pandas as pd
from PIL import Image

from fyp import config

D = json.loads((config.CONSULT / "deck_data.json").read_text())
T = config.TABLES
PLAN = "https://claude.ai/artifact/5RhYSMRFbPKMAhjD8SjEwG"


def img_b64(name: str, mode: str, width: int = 1400) -> str:
    im = Image.open(config.FIGURES / f"{name}_{mode}.png").convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im = im.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def figure(name: str, alt: str, caption: str, table_html: str = "") -> str:
    light, dark = img_b64(name, "light"), img_b64(name, "dark")
    details = (f'<details><summary>Show the numbers</summary><div class="tbl-wrap">{table_html}</div></details>'
               if table_html else "")
    return (f'<figure class="fig"><img class="img-light" alt="{html.escape(alt)}" src="data:image/png;base64,{light}">'
            f'<img class="img-dark" alt="{html.escape(alt)}" src="data:image/png;base64,{dark}">'
            f'<figcaption>{caption}</figcaption>{details}</figure>')


def table(df: pd.DataFrame, num_cols: list[str] = ()) -> str:
    head = "".join(f'<th scope="col"{" class=num" if c in num_cols else ""}>{html.escape(str(c))}</th>' for c in df.columns)
    rows = "".join("<tr>" + "".join(f'<td{" class=num" if c in num_cols else ""}>{html.escape(str(v))}</td>'
                                    for c, v in zip(df.columns, r)) + "</tr>" for r in df.itertuples(index=False))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"


minus = lambda v, d=1: ("−" if v < 0 else "") + f"{abs(v):.{d}f}"
sgn = lambda v, d=1: ("−" if v < 0 else "+" if v > 0 else "") + f"{abs(v):.{d}f}"

# ---- tables under the figures ----
lc = pd.read_csv(T / "liquidity_costs.csv")
core = lc[(lc["group"] == "core") & (lc["status"] == "trading")].sort_values("median_value_sgd", ascending=False)
t_liq = table(pd.DataFrame({
    "Counter": [f"{n} ({c})" for n, c in zip(core["name"], core["code"])],
    "Median daily value": [f"S${v / 1e6:,.2f}M" if v >= 1e6 else f"S${v / 1e3:,.0f}k" for v in core["median_value_sgd"]],
    "Last price": [f"S${v:.3f}" for v in core["last_price"]],
    "Round trip": [f"{v:.2f}%" for v in core["round_trip_floor_pct"]],
}), ["Median daily value", "Last price", "Round trip"])

pt = pd.read_csv(T / "passthrough_daily.csv")
ptc = pt[pt["group"] == "core"].sort_values("beta_dimson", ascending=False)
t_time = table(pd.DataFrame({
    "Counter": [f"{n} ({c})" for n, c in zip(ptc["name"], ptc["code"])],
    "Underlying": ptc["underlying"],
    "Same day": ptc["beta_same_day"].map(lambda v: minus(v, 2)),
    "Dimson": ptc["beta_dimson"].map(lambda v: minus(v, 2)),
    "Next-day share": ptc["next_day_share"].map(lambda v: "" if pd.isna(v) else f"{100 * v:.0f}%"),
    "Note": ptc["data_caveat"].fillna("").map(lambda v: "palm series unreliable" if v else ""),
}), ["Same day", "Dimson", "Next-day share"])

wk = pd.read_csv(T / "passthrough_weekly_r2.csv")
wk = wk[wk["code"].isin([c.code for c in config.CORE])].sort_values("added_by_commodity", ascending=False)
t_r2 = table(pd.DataFrame({
    "Counter": [f"{n} ({c})" for n, c in zip(wk["name"], wk["code"])],
    "STI alone": wk["r2_sti"].map(lambda v: f"{v:.2f}"),
    "STI plus commodity": wk["r2_sti_plus_commodity"].map(lambda v: f"{v:.2f}"),
    "Added": (100 * wk["added_by_commodity"]).map(lambda v: f"{v:.1f} pts"),
}), ["STI alone", "STI plus commodity", "Added"])

lev = pd.read_csv(T / "levy_event_cars.csv")
l0 = lev[lev["window"] == "[0,+0]"]
t_lev = table(pd.DataFrame({
    "Event": l0["event_id"] + " · " + l0["event"],
    "First session": l0["first_session"],
    "Indonesian, SGX": l0["CAR Indonesian growers, SGX"].map(lambda v: f"{sgn(100 * v)}%"),
    "Malaysian, Bursa": l0["CAR Malaysian growers, Bursa"].map(lambda v: f"{sgn(100 * v)}%"),
    "Gap": l0["gap SGX-Indonesian minus Malaysian"].map(lambda v: f"{sgn(100 * v)} pts"),
    "t": l0["t gap"].map(lambda v: minus(v)),
    "Confidence": l0["confidence"],
}), ["Indonesian, SGX", "Malaysian, Bursa", "Gap", "t"])

pw = pd.read_csv(T / "synthetic_ic_power.csv")
pv = pw.pivot(index="months", columns="ic", values="power_mc")
t_pow = table(pd.DataFrame({"Months": pv.index.astype(str),
                            **{f"IC {c:.2f}": (100 * pv[c]).map(lambda v: f"{v:.0f}%") for c in pv.columns},
                            "Detectable IC": pw.groupby("months")["mde_analytic"].first().map(lambda v: f"{v:.2f}").values}),
              [f"IC {c:.2f}" for c in pv.columns] + ["Detectable IC"])

summ = pd.read_csv(T / "plumbing_summary.csv", index_col=0)
t_plumb = table(pd.DataFrame({
    "Series": summ.index,
    "Return a year": summ["annual_return"].map(lambda v: f"{100 * v:.1f}%"),
    "Volatility": summ["volatility"].map(lambda v: f"{100 * v:.1f}%"),
    "Sharpe": summ["sharpe_rf0"].map(lambda v: f"{v:.2f}"),
    "Max drawdown": summ["max_drawdown"].map(lambda v: f"{minus(100 * v, 0)}%"),
}), ["Return a year", "Volatility", "Sharpe", "Max drawdown"])

syn = D["synthetic"]
PL, LV, PO = D["plumbing"], D["levy"], D["power"]
nd = D["timing"]["next_day_share"]
r2 = D["weekly_r2"]["added_pp"]

CSS = (config.ROOT / "tools" / "brief.css").read_text()

body = f"""
<div class="page">
<header class="masthead">
  <div>
    <p class="eyebrow">NTU · EEE · FYP A1088-261 · <b>Consultation brief</b></p>
    <h1>What the first data says, and eight decisions to settle</h1>
    <p class="question">Preliminary results from free data, for the meeting with A/P Wong Jia Yiing, Patricia.</p>
  </div>
  <dl class="facts">
    <dt>Meeting</dt><dd>Thu 22 Oct 2026, 4.30pm, Zoom</dd>
    <dt>Student</dt><dd>Arkana Richie Kalalo</dd>
    <dt>Prepared</dt><dd>21 October 2026</dd>
    <dt>Plan</dt><dd><a href="{PLAN}">Project plan v2</a></dd>
  </dl>
</header>

<section>
  <div class="sec-head"><span class="sec-num">01</span><h2>Opening: three findings</h2></div>
  <div class="col"><p class="lede">Since the 14 September proposal I read the 2026 project in this group (Wijaya), wrote plan v2, built the data pipeline (28 equities and 23 market series, daily from 2013) and ran the first checks. Three results bear on direction.</p></div>
  <div class="stats">
    <div class="stat"><p class="v">{round(100 * min(nd))}–{round(100 * max(nd))}%</p><p class="k">of a commodity move reaches SGX counters in the next session, so same-day regressions understate pass-through by about half.</p></div>
    <div class="stat"><p class="v">{minus(LV['gap_ban'])} pts</p><p class="k">Indonesian minus Malaysian growers in the first session after the 2022 export-ban announcement, t = {minus(LV['t_gap_ban'])}.</p></div>
    <div class="stat"><p class="v">{min(r2):.1f}–{round(max(r2))} pts</p><p class="k">of weekly return variance explained by each counter's commodity. The rest is firm-specific.</p></div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="sec-num">02</span><h2>Evidence</h2></div>
  <div class="col"><p class="note">All numbers come from free data (Yahoo Finance, FRED, SGX) and are preliminary. Daily palm-oil results are unreliable for the reason in section 5.</p></div>

  <h3>The universe and its trading costs</h3>
  {figure("liquidity_dots", "Dot plot of median daily traded value per counter on a log scale, with a S$100k filter line; 15 of 17 trading counters clear it.",
          "Fifteen of the seventeen core counters still trading clear S$100k a day; twelve clear S$1M. A round trip that crosses one tick costs 0.36% for Keppel and 2.08% for Golden Agri and Rex, including fees of 0.13% a side with GST.", t_liq)}

  <h3>Timing: the next session carries much of the response</h3>
  {figure("passthrough_dumbbell", "Dumbbell chart: same-day sensitivity against Dimson sensitivity per counter; every Dimson estimate is larger.",
          f"Commodities settle after the 17:00 SGX close, so {round(100 * min(nd))} to {round(100 * max(nd))}% of the response appears in the next session, with lag t-statistics up to 10. The result holds with Brent spot instead of futures.", t_time)}

  <h3>Pass-through drifts over time</h3>
  {figure("kalman_5TP", "Line chart of CNMC Goldmine's sensitivity to gold from 2014 to 2026: Kalman estimate against a noisier rolling window.",
          f"CNMC's sensitivity to gold went from {D['drift']['start_2014']:.2f} to {D['drift']['end']:.2f}; Rex's sensitivity to Brent ranges {D['drift']['rex_min']:.2f} to {D['drift']['rex_max']:.2f}. A fixed beta would be wrong for both, and the rolling window is too noisy on its own.")}
  {figure("kalman_5WH", "Line chart of Rex International's sensitivity to Brent from 2014 to 2026.", "Rex International against Brent, same method.")}

  <h3>How much of the return is the commodity</h3>
  <div class="col"><p>Weekly R-squared added by each counter's commodity, over the STI alone. At portfolio level the commodity matters more: the sector basket's R-squared rises from {D['basket_r2']['sti_only']:.2f} with the STI alone to {D['basket_r2']['with_commodities']:.2f} with commodity factors.</p></div>
  <div class="tbl-wrap">{t_r2}</div>

  <h3>The export-ban natural experiment</h3>
  {figure("levy_ban_2022", "Line chart of cumulative abnormal returns around the 2022 export ban: Indonesian growers fall, Malaysian growers rise on the announcement.",
          f"Gap {minus(LV['gap_ban'])} points on the ban announcement (t = {minus(LV['t_gap_ban'])}) and {sgn(LV['gap_lift'])} when the lifting was announced (t = {minus(LV['t_gap_lift'])}). Routine levy changes show no measurable effect. Some event dates still need checking against primary sources.", t_lev)}

  <h3>Validation and power</h3>
  {figure("synthetic_recovery", "Line chart of a planted sensitivity against Kalman estimates with and without the next-day term.",
          f"On synthetic counters the Kalman error is {syn['rmse_with_lag']:.2f} with the next-day term and {syn['rmse_same_day']:.2f} without it, which misses {round(100 * syn['share_missed'])}% of the response. A planted 30% asymmetry was detected in {syn['asym_detected']} of {syn['asym_runs']} runs, so that test is weak.")}
  {figure("power_curve", "Line chart of the smallest detectable information coefficient against months of data for 12, 18 and 30 counters.",
          f"An 18-month lockbox detects only IC ≥ {PO['lockbox_18']:.2f}; eight to ten years of walk-forward data detect {PO['wf_120']:.2f} to {PO['wf_96']:.2f}. The Monte Carlo rejection rates below match the formula, with false positives of {100 * syn['false_pos_min']:.0f} to {100 * syn['false_pos_max']:.1f}%.", t_pow)}

  <h3>Plumbing run: a naive sector basket</h3>
  {figure("plumbing_basket", "Line chart of S$100 invested in January 2014: equal-weight sector basket net of costs against the STI total return.",
          f"No signal is used. The basket returned {PL['ret_basket']:.1f}% a year net of costs (Sharpe {PL['sharpe_basket']:.2f}, drawdown {minus(PL['dd_basket'], 0)}%) against {PL['ret_sti']:.1f}% for the STI total return (Sharpe {PL['sharpe_sti']:.2f}). Jensen's alpha: {minus(PL['alpha_capm'])}% a year against the STI alone and {minus(PL['alpha_full'])}% with commodity factors (t = {minus(PL['t_alpha_full'])}).", t_plumb)}
</section>

<section>
  <div class="sec-head"><span class="sec-num">03</span><h2>Eight decisions to formalise</h2></div>
  <div class="decisions">
    <div class="dec"><p class="id">D1 · Commodity data</p><p class="rec">Bloomberg at the Business Library for daily FCPO, Newcastle coal and freight; free monthly series as the fallback; never the free daily palm series.</p><p class="why">The free palm series is a monthly-average swap (section 5). Decision point: 31 October.</p></div>
    <div class="dec"><p class="id">D2 · Universe</p><p class="rec">S$100k median daily traded value over the trailing year, applied point-in-time each month: 15 counters today.</p><p class="why">Higher thresholds remove few names but cost power: with 12 counters the detectable IC over eight years rises from 0.07 to 0.09.</p></div>
    <div class="dec"><p class="id">D3 · Horizons</p><p class="rec">Models predict 5- and 20-day residual returns; the strategy rebalances monthly and executes overnight information at the next open.</p><p class="why">Round trips cost up to 2.1%; closes are unchanged on a third of days for the penny counters.</p></div>
    <div class="dec"><p class="id">D4 · Machine learning</p><p class="rec">Four models as in Wijaya (2026): ridge, XGBoost, LSTM and TFT, with the TFT dropped first if time runs short.</p><p class="why">Mirrors the prior work she supervised and adds a linear floor. The environment is installed and tested.</p><p class="ask">Ask whether she wants the deep models, given about eighteen counters.</p></div>
    <div class="dec"><p class="id">D5 · Fundamentals</p><p class="rec">A sector-relative F-score ranking each reporting period, plus the panel test of what explains pass-through.</p><p class="why">The brief asks for a ranking methodology. Free statements cover FY2021 onward only.</p><p class="ask">Ask whether the sector-relative version is acceptable as the stage 01 method.</p></div>
    <div class="dec"><p class="id">D6 · Aim 1 framing</p><p class="rec">Commodity sensitivities are significant, drift over time and arrive partly the next day, but explain a minority of weekly variance, and removing them changes measured alpha.</p><p class="why">Evidence above; most of the return is left for the FA, NA and TA layers.</p></div>
    <div class="dec"><p class="id">D7 · News</p><p class="rec">Event studies on residuals with severity tiers, and the export-levy experiment as the headline test.</p><p class="why">Large, surprising shocks move the residual; routine levy changes do not. Announcement timestamps must come from Bloomberg or Factiva.</p></div>
    <div class="dec"><p class="id">D8 · Validation</p><p class="rec">The walk-forward record with bootstrap intervals is the evidence; the lockbox is a sign check; nulls are stated against their detectable effect.</p><p class="why">An 18-month lockbox can only detect implausibly strong signals.</p></div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="sec-num">04</span><h2>Questions for Prof. Wong</h2></div>
  <ol class="qs">
    <li>Which title was registered on Stafflink before 5 October: the proposal's "An FA–NA–TA Trading Framework for SGX Energy and Commodity Equities", or an alternative?</li>
    <li>The interim report: its date, length and format, and what the video must cover.</li>
    <li>Is a sector-relative F-score ranking acceptable as the stage 01 method?</li>
    <li>Four models, as in Wijaya (2026), or ridge and XGBoost only?</li>
    <li>May Wijaya (2026) be cited as prior work in this group?</li>
    <li>Does EEE require a declaration on the use of generative AI tools in the reports?</li>
    <li>Any advice on Bloomberg terminal access, or data from previous students?</li>
  </ol>
</section>

<section>
  <div class="sec-head"><span class="sec-num">05</span><h2>Gaps in the free data</h2></div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th scope="col" style="width:24%">Gap</th><th scope="col">What was found</th><th scope="col" style="width:26%">Fix</th></tr></thead>
      <tbody>
        <tr><td>Daily palm oil</td><td>The free series (CPO=F) is CME's calendar future, settled on the monthly average of Bursa FCPO. First-of-month moves are 3.9 times normal, late-month moves 0.27 times early-month, and it moved −0.7% on the first session after the ban announcement.</td><td>Bloomberg FCPO, third month</td></tr>
        <tr><td>Fundamentals before 2021</td><td>Free statements cover FY2021 to FY2025, with almost no quarterly data.</td><td>Bloomberg or annual reports</td></tr>
        <tr><td>Delisted counter</td><td>Golden Energy and Resources (delisted September 2023) is not in free data; leaving it out overstates sector returns.</td><td>Bloomberg price history</td></tr>
        <tr><td>Event timestamps</td><td>The SGX announcements API is closed to scripts.</td><td>Bloomberg event calendar or Factiva</td></tr>
        <tr><td>Risk-free rate</td><td>FRED has no Singapore short rate; Sharpe ratios and alphas use zero for now.</td><td>SORA or the 3-month T-bill from MAS</td></tr>
        <tr><td>Interra Resources</td><td>No trades since 31 January 2025.</td><td>Confirm whether it is suspended</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <div class="sec-head"><span class="sec-num">06</span><h2>Next three weeks</h2></div>
  <div class="weeks">
    <div class="wk"><p class="when">S1 W10 · this week</p><p class="what">Data</p><ul><li>Bloomberg session using the shopping list</li><li>Factiva test export</li><li>Commodity data decision by 31 October</li></ul></div>
    <div class="wk"><p class="when">S1 W11</p><p class="what">Aim 1</p><ul><li>Rerun pass-through with Bloomberg FCPO</li><li>Freeze the harness and seal the lockbox</li><li>Write up the synthetic tests</li></ul></div>
    <div class="wk"><p class="when">S1 W12 to W13</p><p class="what">Interim report</p><ul><li>Chapters 1 to 4</li><li>The interim video</li></ul></div>
  </div>
  <div class="col"><p class="note">Everything here is rebuilt by <code>./run_all.sh</code> in <code>~/Desktop/FYP/fyp-pipeline</code>. The slide draft is <code>consultation/deck_draft.pptx</code> and the text brief is <code>consultation/decision_brief.md</code>.</p></div>
</section>

<footer><span>A1088-261 · Consultation brief · 21 October 2026</span><span>Arkana Richie Kalalo · Supervisor A/P Wong Jia Yiing, Patricia</span></footer>
</div>
"""

page = ('<title>A1088-261 Consultation Brief</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">\n'
        f"<style>\n{CSS}\n</style>\n{body}")
out = config.CONSULT / "brief.html"
out.write_text(page)
print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
