// Builds interim/FYP_Interim_Progress.pptx: the plan as a table, then work done so far (modelled on section 2
// of the sample interim report). Numbers come from interim/progress_data.json and consultation/deck_data.json.
// Run from the repo root:
//   python -I scripts/20_deck_data.py && python -I scripts/22_progress_data.py
//   NODE_PATH=tools/deck/node_modules node tools/deck/build_progress_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const SKILL_THEME = "/Users/rikalalo/.claude/skills/synced/88398549-97ff-4565-9594-01a085acc119_da635b9d-c1a4-46c3-ac50-6f8819d6a5dc/pptx/scripts/apply_theme.js";
const ROOT = path.resolve(__dirname, "../..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "consultation/deck_data.json"), "utf8"));
const P = JSON.parse(fs.readFileSync(path.join(ROOT, "interim/progress_data.json"), "utf8"));
const OUT = path.join(ROOT, "interim/FYP_Interim_Progress.pptx");
const ASOF = "23 October 2026";

const THEME = {
	name: "A1088 Teal",
	headFontFace: "Cambria",
	bodyFontFace: "Calibri",
	colors: {
		dk1: "0E1A18", lt1: "FFFFFF", dk2: "0B4F47", lt2: "EEF3F1",
		accent1: "0B5F55", accent2: "A85B16", accent3: "3E9D8D", accent4: "5B6B67",
		accent5: "8AC4B4", accent6: "E3B65C", hlink: "0B5F55", folHlink: "5B6B67",
	},
};
// Hex copies, for the options that only take hex (chart colours, grid lines, table borders)
const HEX = { ink2: "2C3B37", muted: "5B6B67", grid: "E2E8E6", border: "D6DEDB", teal: "0B5F55", tealSoft: "8AC4B4", amber: "A85B16" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Arkana Richie Kalalo";
pres.title = "A1088-261 interim progress";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const FOOT = `A1088-261 · Interim progress · ${ASOF}`;

// ---------- layouts ----------
pres.defineSlideMaster({
	title: "TITLE",
	background: { color: C.text2 },
	objects: [
		{ placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.4, w: 11.7, h: 2.5, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1, align: "left", valign: "bottom" }, text: "" } },
		{ placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 0.7, fontSize: 22, color: C.background2, align: "left", valign: "top" }, text: "" } },
		{ placeholder: { options: { name: "meta", type: "body", x: 0.8, y: 6.0, w: 11.7, h: 0.8, fontSize: 16, color: C.accent5, align: "left", valign: "top" }, text: "" } },
	],
});
pres.defineSlideMaster({
	title: "CONTENT",
	background: { color: C.background1 },
	objects: [
		{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontFace: "Cambria", fontSize: 36, bold: true, color: C.text1, align: "left", valign: "middle" }, text: "" } },
		{ text: { text: FOOT, options: { x: 0.6, y: 7.02, w: 9.0, h: 0.3, fontSize: 10, color: C.accent4, align: "left", valign: "middle", margin: 0 } } },
	],
	slideNumber: { x: 12.1, y: 7.02, w: 0.6, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
});

// ---------- helpers (each call builds fresh option objects: pptxgenjs mutates them) ----------
const NB = "\u00A0"; // keeps 't = -5.9' on one line
const tstat = (v) => `t${NB}=${NB}${minus(v)}`;
const minus = (v, d = 1) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
const pctRange = (a) => `${Math.round(100 * Math.min(...a))}–${Math.round(100 * Math.max(...a))}%`;
const ptsRange = (a) => `${Math.min(...a).toFixed(1)}–${Math.round(Math.max(...a))} pts`;

function tile(slide, o) {
	const chip = !!o.chip;
	slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Tile: ${o.big}` });
	if (chip) slide.addText(o.chip, { x: o.x + 0.25, y: o.y + 0.12, w: o.w - 0.5, h: 0.26, fontSize: 11, bold: true, charSpacing: 2, color: C.accent2, valign: "top", margin: 0, isTextBox: true, objectName: `Tile tag: ${o.chip}` });
	slide.addText(o.big, { x: o.x + 0.25, y: o.y + (chip ? 0.36 : 0.15), w: o.w - 0.5, h: 0.58, fontFace: "Cambria", fontSize: o.bigSize || 28, bold: true, color: C.accent1, valign: "top", margin: 0, isTextBox: true, objectName: `Tile value: ${o.big}` });
	const ly = o.y + (chip ? 0.95 : 0.82);
	slide.addText(o.label, { x: o.x + 0.25, y: ly, w: o.w - 0.5, h: o.y + o.h - ly - 0.06, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: `Tile label: ${o.big}` });
}
function numbered(slide, n, o) {
	slide.addShape(pres.shapes.OVAL, { x: o.x, y: o.y + 0.02, w: 0.42, h: 0.42, fill: { color: C.accent5 }, line: { type: "none" }, objectName: `Number ${n}` });
	slide.addText(String(n), { x: o.x, y: o.y + 0.02, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.text2, align: "center", valign: "middle", margin: 0, isTextBox: true });
	slide.addText(o.text, { x: o.x + 0.62, y: o.y, w: o.w, h: o.h, fontSize: 15, color: C.background1, valign: "top", margin: 0, isTextBox: true });
}
function caption(slide, text, y) {
	slide.addText(text, { x: 0.6, y, w: 12.1, h: 0.45, fontSize: 11, italic: true, color: C.accent4, valign: "top", margin: 0, isTextBox: true, objectName: "Caption" });
}
function chartOpts(extra) {
	return Object.assign({
		catAxisLabelColor: HEX.ink2, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
		valAxisLabelColor: HEX.muted, valAxisLabelFontSize: 10, valAxisLabelFontFace: "+mn-lt",
		valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" },
		dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: HEX.ink2,
		legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: HEX.ink2,
		valAxisTitleFontFace: "+mn-lt", valAxisTitleFontSize: 10, valAxisTitleColor: HEX.muted,
		catAxisTitleFontFace: "+mn-lt", catAxisTitleFontSize: 10, catAxisTitleColor: HEX.muted,
	}, extra);
}

// ======================================================================
// Part 1: the plan
// ======================================================================
pres.addSection({ title: "Plan" });

let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Plan" });
s.addText("An FA–NA–TA Trading Framework for SGX Energy and Commodity Equities", { placeholder: "title" });
s.addText("Interim progress: the plan and the work done so far", { placeholder: "subtitle" });
s.addText(`Arkana Richie Kalalo · Project A1088-261\nSupervisor: A/P Wong Jia Yiing, Patricia · ${ASOF}`, { placeholder: "meta" });
s.addNotes("This update has two parts: the plan, then the work done so far. Everything shown is preliminary and comes from free data, ahead of the Bloomberg pull.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Plan" });
s.addText("The plan in seven stages", { placeholder: "title" });
const head = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 } } });
const FILL = { Done: C.accent5, "In progress": C.accent6, Planned: C.background2 };
const stages = [
	["1 · Groundwork", "S1 W1–W9", "Literature review, universe, title and plan", "Proposal and plan v2; research gaps", "Done"],
	["2 · Data and infrastructure", "S1 W6–W12", "Data pipeline, SGX cost model, synthetic tests, harness", "Point-in-time panel; frozen harness; sealed lockbox", "In progress"],
	["3 · Aim 1: pass-through", "S1 W10–W13", "Kalman and Dimson estimates of commodity sensitivity", "Residual series; interim report and video", "In progress"],
	["4 · Aims 2 and 3: FA and NA", "Break–S2 W6", "Fundamental ranking; Factiva events and sentiment", "Ranked list per period; event database; levy result", "Planned"],
	["5 · Aim 4: models", "S2 W4–W9", "Ridge, XGBoost, LSTM and TFT on one harness", "Model comparison; attribution by feature family", "Planned"],
	["6 · Aim 5: strategy", "S2 W8–W11", "Cost-aware monthly strategy; lockbox opened once", "Alpha with intervals; one lockbox result", "Planned"],
	["7 · Reporting", "S2 W8–exams", "Final report, demonstration and oral presentation", "Report; dashboard demo; oral", "Planned"],
];
const body = (t, bold) => ({ text: t, options: { color: C.text1, bold: !!bold } });
const rows = [[head("Stage"), head("Period"), head("Focus"), head("Key deliverables"), head("Status")]].concat(
	stages.map((r, i) => {
		const bg = i % 2 ? C.background1 : C.background2;
		return [
			{ text: r[0], options: { bold: true, color: C.text1, fill: { color: bg } } },
			{ text: r[1], options: { color: C.text1, fill: { color: bg } } },
			{ text: r[2], options: { color: C.text1, fill: { color: bg } } },
			{ text: r[3], options: { color: C.text1, fill: { color: bg } } },
			{ text: r[4], options: { bold: true, color: C.text1, fill: { color: FILL[r[4]] }, align: "center" } },
		];
	}));
s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [2.5, 1.5, 3.5, 3.2, 1.4], fontSize: 14, rowH: [0.45].concat(stages.map(() => 0.62)), valign: "middle", margin: [0.04, 0.12, 0.04, 0.12], border: { type: "solid", pt: 0.75, color: HEX.border }, objectName: "Plan table" });
caption(s, `Status as of ${ASOF}. Milestones: interim report and video S1 W13; final report S2 W12–W13; oral presentation in the exam weeks. Week numbers follow the plan and are to be confirmed against the EEE key-dates page.`, 6.45);
s.addNotes("Seven stages across two semesters. Stage 1 is complete. Stages 2 and 3 are under way: the pipeline, cost model and synthetic tests are built, and the next steps are the residual series for every counter and freezing the harness. Fundamentals, news, the model comparison and the strategy follow over the break and in Semester 2.");

// ======================================================================
// Part 2: work done so far
// ======================================================================
pres.addSection({ title: "Work done so far" });

// ---- Stage 1: literature review and problem framing ----
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Work done so far" });
s.addText("Stage 1: literature and problem framing", { placeholder: "title" });
[
	["PASS-THROUGH", "Commodity equities are levered claims on their underlying, and the response is asymmetric in a direction that differs by industry (Sadorsky 2001; Ramos and Veiga 2011)."],
	["RESIDUALS", "Momentum and event effects are cleaner on residual returns than on raw returns, so the commodity is removed first (Blitz et al. 2011; MacKinlay 1997)."],
	["MODELS AND COSTS", "Tree models match or beat deep networks on tabular data, and trading costs erase most paper profits (Grinsztajn et al. 2022; Fischer and Krauss 2018). The 2026 project in this group found XGBoost the most consistent of four models."],
].forEach(([chip, text], i) => {
	const y = 1.5 + i * 1.75, h = 1.55;
	s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 7.6, h, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Finding card ${chip}` });
	s.addText(chip, { x: 0.9, y: y + 0.17, w: 7.0, h: 0.28, fontSize: 12, bold: true, charSpacing: 2, color: C.accent2, margin: 0, isTextBox: true });
	s.addText(text, { x: 0.9, y: y + 0.5, w: 7.0, h: h - 0.6, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true });
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.5, y: 1.5, w: 4.2, h: 5.05, rectRadius: 0.06, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Gap and question card" });
s.addText("THE GAP", { x: 8.8, y: 1.75, w: 3.6, h: 0.28, fontSize: 12, bold: true, charSpacing: 2, color: C.accent5, margin: 0, isTextBox: true });
s.addText("Pass-through evidence comes from North American and European oil and gas. SGX energy and commodity equities are dominated by agri-commodity producers, a universe this literature has not examined.", { x: 8.8, y: 2.08, w: 3.6, h: 1.85, fontSize: 14, color: C.background1, valign: "top", margin: 0, isTextBox: true });
s.addText("THE QUESTION", { x: 8.8, y: 4.15, w: 3.6, h: 0.28, fontSize: 12, bold: true, charSpacing: 2, color: C.accent5, margin: 0, isTextBox: true });
s.addText("Once the commodity is removed, does fundamental, news or technical information predict what remains, and does a more complex model extract more of it?", { x: 8.8, y: 4.48, w: 3.6, h: 1.95, fontFace: "Cambria", fontSize: 18, italic: true, color: C.background1, valign: "top", margin: 0, isTextBox: true });
s.addNotes("The literature gives three starting points. Commodity equities respond to their commodity, with an asymmetry that depends on the industry. Residual returns are the better object to model. And machine-learning gains are small once costs are charged. The gap is the universe: the pass-through evidence is built on North American and European oil and gas, while SGX is dominated by agri-commodity producers. The central question is on the right, and each of the five aims answers part of it.");

// ---- Stage 2: data pipeline ----
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Work done so far" });
s.addText("Stage 2: a reproducible data pipeline", { placeholder: "title" });
const steps = [
	["SOURCES", "Free data", `Yahoo Finance (${P.equities_downloaded} equities, ${P.series_yahoo} series), FRED (${P.series_fred} series), and an SGX snapshot of ${P.sgx_snapshot_securities.toLocaleString("en-US")} securities`],
	["RAW", "Read-only", "Each download goes to its own dated folder and is never edited"],
	["PANEL", "Clean panel", "One table per field, each market on its own calendar; holiday rows removed"],
	["OUTPUTS", "One command", "Tables, light and dark figures and both briefs rebuild in about four minutes"],
];
const BW = 2.55, GAP = (12.1 - 4 * BW) / 3, BY = 1.5, BH = 2.2;
steps.forEach(([chip, headText, text], i) => {
	const x = 0.6 + i * (BW + GAP);
	s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: BY, w: BW, h: BH, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Pipeline step ${chip}` });
	s.addText(chip, { x: x + 0.22, y: BY + 0.15, w: BW - 0.44, h: 0.26, fontSize: 11, bold: true, charSpacing: 2, color: C.accent2, margin: 0, isTextBox: true });
	s.addText(headText, { x: x + 0.22, y: BY + 0.43, w: BW - 0.44, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true });
	s.addText(text, { x: x + 0.22, y: BY + 0.9, w: BW - 0.44, h: BH - 0.98, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
	if (i < 3) s.addShape(pres.shapes.LINE, { x: x + BW + 0.08, y: BY + BH / 2, w: GAP - 0.16, h: 0, line: { color: C.accent1, width: 2, endArrowType: "triangle" }, objectName: `Pipeline arrow ${i + 1}` });
});
tile(s, { x: 0.6, y: 4.0, w: 3.9, h: 1.85, chip: "COVERAGE", big: `${P.equities_downloaded} + ${P.series_total}`, label: "equities and market series, daily since January 2013" });
tile(s, { x: 4.7, y: 4.0, w: 3.9, h: 1.85, chip: "LIQUIDITY", big: `${P.pass_100k} of ${P.core_trading}`, label: "trading core counters clear S$100k median daily value" });
tile(s, { x: 8.8, y: 4.0, w: 3.9, h: 1.85, chip: "COSTS", big: `${P.round_trip_min.toFixed(2)}–${P.round_trip_max.toFixed(2)}%`, label: `round trip, ${P.round_trip_min_name} to ${P.round_trip_max_name}: one tick plus fees` });
caption(s, "Golden Energy and Resources (delisted 2023) is missing from free data, and Interra Resources has not traded since January 2025.", 6.1);
s.addNotes("The pipeline downloads free data once into dated folders, builds one table per field on each market's own calendar, and rebuilds every table, figure and brief with one command. It covers 28 equities, including Indonesian and Malaysian growers for the export-levy test, and 23 market series: indices, commodities, currencies and the VIX. Fifteen of the seventeen core counters still trading clear S$100k a day. The cost model uses the SGX tick schedule, so a round trip costs between 0.36 and 2.08 per cent.");

// ---- Stage 3: Aim 1 first results ----
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Work done so far" });
s.addText("Stage 3: pass-through, first results", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
	{ name: "Same-day OLS", labels: D.timing.labels, values: D.timing.same_day },
	{ name: "Dimson: lag + same day + lead", labels: D.timing.labels, values: D.timing.dimson },
], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.75, barDir: "bar", barGrouping: "clustered", chartColors: [HEX.tealSoft, HEX.teal], barGapWidthPct: 40,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisLabelFormatCode: "0.0",
	valAxisMinVal: 0, showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Sensitivity to a 1% commodity move",
}));
tile(s, { x: 9.15, y: 1.45, w: 3.55, h: 1.5, big: pctRange(D.timing.next_day_share), label: "of the response arrives in the next SGX session" });
tile(s, { x: 9.15, y: 3.05, w: 3.55, h: 1.5, big: `${D.drift.start_2014.toFixed(2)} → ${D.drift.end.toFixed(2)}`, label: "CNMC's sensitivity to gold, 2014 to now (Kalman)" });
tile(s, { x: 9.15, y: 4.65, w: 3.55, h: 1.5, big: ptsRange(D.weekly_r2.added_pp), label: "of weekly variance explained by each counter's commodity" });
caption(s, "Methods compared: same-day OLS, Dimson lead-lag, weekly up and down moves, Kalman filter. Daily log returns, 2014 to October 2026. Palm counters omitted until Bloomberg FCPO replaces the free palm series.", 6.35);
s.addNotes("This is Aim 1. Commodities settle after the SGX close, so a same-day regression catches only part of the response: between 39 and 76 per cent arrives in the next session, and Dimson's lead-lag beta roughly doubles the measured sensitivity. The sensitivity also drifts: CNMC's response to gold rose from 0.44 to 1.60, which is why the Kalman filter is the primary estimator. The commodity explains between 0.4 and 19 points of weekly variance per counter, so most of each return is left for the fundamental, news and technical layers.");

// ---- Early tests ----
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Work done so far" });
s.addText("Three early tests of the method", { placeholder: "title" });
s.addChart(pres.charts.BAR, D.levy.series.map(g => ({ name: g.name, labels: D.levy.events, values: g.values })), chartOpts({
	x: 0.6, y: 1.45, w: 7.7, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [HEX.teal, HEX.tealSoft, HEX.amber], barGapWidthPct: 60,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0",
	showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Abnormal return, first session (%)",
}));
tile(s, { x: 8.55, y: 1.45, w: 4.15, h: 1.6, chip: "EXPORT-BAN TEST", big: `${minus(D.levy.gap_ban)} pts`, label: `Indonesian minus Malaysian growers on the 2022 ban announcement; ${tstat(D.levy.t_gap_ban)}` });
tile(s, { x: 8.55, y: 3.15, w: 4.15, h: 1.6, chip: "SYNTHETIC TESTS", big: `${D.synthetic.rmse_with_lag.toFixed(2)} vs ${D.synthetic.rmse_same_day.toFixed(2)}`, label: "Kalman error with and without the next-day term, on simulated counters" });
tile(s, { x: 8.55, y: 4.85, w: 4.15, h: 1.6, chip: "PLUMBING RUN", big: `${minus(D.plumbing.alpha_full)}% a year`, label: `Alpha of a naive sector basket after costs (${tstat(D.plumbing.t_alpha_full)}); Sharpe ${D.plumbing.sharpe_basket.toFixed(2)} vs ${D.plumbing.sharpe_sti.toFixed(2)} for the STI` });
caption(s, "Left: equal-weight portfolios against each market's own index; routine levy changes show no effect and some event dates still need checking. The plumbing run uses no signal: it tests the cost model and the alpha regression.", 6.55);
s.addNotes("Three tests of the machinery. First, the export-levy natural experiment: when Indonesia announced its 2022 export ban, SGX-listed Indonesian growers fell against their market while Malaysian growers rose, an eleven-point gap with a t-statistic near minus six, and it reversed when the lifting was announced. Second, synthetic counters with planted answers: the Kalman filter recovers the sensitivity only with the next-day term. Third, a plumbing run: a naive equal-weight basket, costed tick by tick, earns no alpha, which sets the bar any signal has to clear.");

// ---- Challenges and next steps ----
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Work done so far" });
s.addText("Challenges so far, and next steps", { placeholder: "title" });
const issues = [
	["Free daily palm-oil series is a monthly-average swap", "Bloomberg FCPO, decided by 31 October; monthly data as the fallback"],
	["Commodities settle after the SGX close", "Dimson lead-lag betas; overnight signals trade at the next open"],
	["Round trips cost up to 2.1% on penny counters", "Monthly rebalancing and a cost-based entry threshold"],
	["About 18 counters: an 18-month lockbox detects only IC ≥ 0.16", "Judge on the walk-forward record; state each null against its detectable size"],
	["Free data gaps: pre-2021 fundamentals, Golden Energy, SGX announcements", "Bloomberg, annual reports and Factiva"],
];
const irows = [[head("Challenge"), head("Response")]].concat(issues.map((r, i) => {
	const bg = i % 2 ? C.background1 : C.background2;
	return [{ text: r[0], options: { bold: true, color: C.text1, fill: { color: bg } } }, { text: r[1], options: { color: C.text1, fill: { color: bg } } }];
}));
s.addTable(irows, { x: 0.6, y: 1.5, w: 8.0, colW: [4.1, 3.9], fontSize: 14, rowH: [0.45].concat(issues.map(() => 0.78)), valign: "middle", margin: [0.04, 0.12, 0.04, 0.12], border: { type: "solid", pt: 0.75, color: HEX.border }, objectName: "Challenges table" });
s.addText("Takeaway: the method behaves on synthetic and real data; the open risks are data access and statistical power, not modelling.", { x: 0.6, y: 6.0, w: 8.0, h: 0.7, fontSize: 15, bold: true, color: C.accent1, valign: "top", margin: 0, isTextBox: true, objectName: "Takeaway" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.9, y: 1.5, w: 3.8, h: 5.2, rectRadius: 0.06, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Next steps card" });
s.addText("NEXT THREE WEEKS", { x: 9.2, y: 1.75, w: 3.3, h: 0.28, fontSize: 12, bold: true, charSpacing: 2, color: C.accent5, margin: 0, isTextBox: true });
[
	"Bloomberg session and a Factiva test export (S1 W10)",
	"Residual series for every counter; freeze the harness and seal the lockbox (S1 W11)",
	"Interim report chapters 1 to 4, and the video (S1 W12–W13)",
].forEach((t, i) => numbered(s, i + 1, { x: 9.2, y: 2.25 + i * 1.2, w: 2.65, h: 1.05, text: t }));
s.addText("Then: fundamentals and news over the break, the model comparison and the strategy in Semester 2.", { x: 9.2, y: 5.85, w: 3.3, h: 0.75, fontSize: 14, color: C.accent5, valign: "top", margin: 0, isTextBox: true });
s.addNotes("Five challenges so far, each with a response already in the plan. The biggest practical one is data: the free palm-oil series cannot be used for daily work, so a Bloomberg session before 31 October matters. The statistical one is power: with about eighteen counters, an eighteen-month lockbox can only detect implausibly strong signals, so the evidence has to come from the full walk-forward record. Next three weeks: Bloomberg and Factiva, then the residual series and the harness, then the interim report and video.");

(async () => {
	fs.mkdirSync(path.dirname(OUT), { recursive: true });
	await pres.writeFile({ fileName: OUT });
	const { applyTheme } = require(SKILL_THEME);
	await applyTheme(OUT, THEME);
	console.log("wrote", OUT);
})();
