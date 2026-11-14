// Builds consultation/deck_draft.pptx from consultation/deck_data.json (written by scripts/20_deck_data.py).
// Run from the repo root:
//   NODE_PATH=tools/deck/node_modules node tools/deck/build_deck.js
// Structured deck: theme colours and fonts, three named layouts, sections, native charts, speaker notes.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const SKILL_THEME = "/Users/rikalalo/.claude/skills/synced/88398549-97ff-4565-9594-01a085acc119_da635b9d-c1a4-46c3-ac50-6f8819d6a5dc/pptx/scripts/apply_theme.js";
const ROOT = path.resolve(__dirname, "../..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "consultation/deck_data.json"), "utf8"));
const OUT = path.join(ROOT, "consultation/deck_draft.pptx");
const PLAN_URL = "https://claude.ai/artifact/5RhYSMRFbPKMAhjD8SjEwG";

const THEME = {
	name: "A1088 Teal",
	headFontFace: "Cambria",
	bodyFontFace: "Calibri",
	colors: {
		dk1: "0E1A18", lt1: "FFFFFF", dk2: "0B4F47", lt2: "EEF3F1",
		accent1: "0B5F55", accent2: "A85B16", accent3: "3E9D8D", accent4: "5B6B67",
		accent5: "8AC4B4", accent6: "D9A441", hlink: "0B5F55", folHlink: "5B6B67",
	},
};
// Hex copies for the options that only take hex (chart colours, grid lines, table borders)
const HEX = { ink: "0E1A18", ink2: "2C3B37", muted: "5B6B67", grid: "E2E8E6", border: "D6DEDB",
	teal: "0B5F55", tealSoft: "8AC4B4", tealMid: "3E9D8D", amber: "A85B16", gray1: "8A9A96", gray2: "BAC6C2" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Arkana Richie Kalalo";
pres.title = "A1088-261 consultation, 22 October 2026";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const FOOT = "A1088-261 · Consultation with A/P Wong · 22 October 2026";

// ---------- layouts ----------
pres.defineSlideMaster({
	title: "TITLE",
	background: { color: C.text2 },
	objects: [
		{ placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.5, w: 11.7, h: 2.4, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1, align: "left", valign: "bottom" }, text: "" } },
		{ placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 0.7, fontSize: 20, color: C.background2, align: "left", valign: "top" }, text: "" } },
		{ placeholder: { options: { name: "meta", type: "body", x: 0.8, y: 6.15, w: 11.7, h: 0.5, fontSize: 14, color: C.accent5, align: "left", valign: "top" }, text: "" } },
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
pres.defineSlideMaster({
	title: "CLOSING",
	background: { color: C.text2 },
	objects: [
		{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.45, w: 12.1, h: 0.95, fontFace: "Cambria", fontSize: 36, bold: true, color: C.background1, align: "left", valign: "middle" }, text: "" } },
		{ text: { text: FOOT, options: { x: 0.6, y: 7.02, w: 9.0, h: 0.3, fontSize: 10, color: C.accent5, align: "left", valign: "middle", margin: 0 } } },
	],
});

// ---------- helpers (each call builds fresh option objects: pptxgenjs mutates them) ----------
function tile(slide, o) {
	const big = o.bigSize || 32;
	slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Tile: ${o.big}` });
	slide.addText(o.big, { x: o.x + 0.25, y: o.y + 0.18, w: o.w - 0.5, h: 0.7, fontFace: "Cambria", fontSize: big, bold: true, color: C.accent1, valign: "top", margin: 0, isTextBox: true, objectName: `Tile value: ${o.big}` });
	slide.addText(o.label, { x: o.x + 0.25, y: o.y + 0.95, w: o.w - 0.5, h: o.h - 1.1, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: `Tile label: ${o.big}` });
}
function numbered(slide, n, o) {
	const dark = !!o.dark;
	slide.addShape(pres.shapes.OVAL, { x: o.x, y: o.y + 0.02, w: 0.42, h: 0.42, fill: { color: dark ? C.accent5 : C.accent1 }, line: { type: "none" }, objectName: `Number ${n}` });
	slide.addText(String(n), { x: o.x, y: o.y + 0.02, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: dark ? C.text2 : C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
	slide.addText(o.text, { x: o.x + 0.62, y: o.y, w: o.w, h: o.h || 0.5, fontSize: o.fontSize || 16, color: dark ? C.background1 : C.text1, valign: "top", margin: 0, isTextBox: true });
}
function caption(slide, text, y) {
	slide.addText(text, { x: 0.6, y: y || 6.5, w: 12.1, h: 0.42, fontSize: 11, italic: true, color: C.accent4, valign: "top", margin: 0, isTextBox: true, objectName: "Caption" });
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
const RIGHT = { x: 9.15, w: 3.55 }; // right-hand column beside an 8.3-inch chart
// Signed numbers with a true minus sign
const sgn = (v, digits = 1) => (v < 0 ? "−" : v > 0 ? "+" : "") + Math.abs(v).toFixed(digits);
const minus = (v, digits = 1) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(digits);
const pctRange = (arr) => `${Math.round(100 * Math.min(...arr))}–${Math.round(100 * Math.max(...arr))}%`;
const ptsRange = (arr) => `${Math.min(...arr).toFixed(1)}–${Math.round(Math.max(...arr))} pts`;

// ======================================================================
// Section 1: context
// ======================================================================
pres.addSection({ title: "Context" });

let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Context" });
s.addText("An FA–NA–TA Trading Framework for SGX Energy and Commodity Equities", { placeholder: "title" });
s.addText("Consultation with A/P Wong Jia Yiing, Patricia · 22 October 2026", { placeholder: "subtitle" });
s.addText("Arkana Richie Kalalo · Project A1088-261 · Plan v2 and preliminary results", { placeholder: "meta" });
s.addNotes("Thank you for making time. In about twenty minutes: what changed since the proposal, the first results from free data, and eight decisions, mostly about data and scope. I would like to leave with answers to the questions on slide 15.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
s.addText("One revised plan, three early findings", { placeholder: "title" });
s.addText("Since the 14 September proposal", { x: 0.6, y: 1.55, w: 6.0, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true });
[
	"Read the 2026 project in this group (Wijaya) and adopted its model comparison as a new Aim 4",
	"Wrote plan v2: ten changes, same title and aims",
	`Built the pipeline: 28 equities and 23 market series, daily from 2013`,
	"Ran first checks on free data, before any Bloomberg pull",
].forEach((t, i) => numbered(s, i + 1, { x: 0.6, y: 2.25 + i * 1.0, w: 5.4, h: 0.8, text: t }));
tile(s, { x: 7.0, y: 1.55, w: 5.7, h: 1.55, big: pctRange(D.timing.next_day_share), label: "of a commodity move reaches SGX counters in the next session" });
tile(s, { x: 7.0, y: 3.3, w: 5.7, h: 1.55, big: `${minus(D.levy.gap_ban)} pts`, label: `Indonesian minus Malaysian growers on the export-ban announcement (t = ${minus(D.levy.t_gap_ban)})` });
tile(s, { x: 7.0, y: 5.05, w: 5.7, h: 1.55, big: ptsRange(D.weekly_r2.added_pp), label: "of weekly return variance explained by each counter's commodity" });
s.addNotes("Four things since the proposal. The three numbers on the right are the findings that bear on direction: timing, the export-ban natural experiment, and how much of the return the commodity actually explains. All of it is from free data, so it is preliminary.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
s.addText("What the 2026 project in this group teaches", { placeholder: "title" });
[
	["ENERGY", "Its energy stock was the hardest to trade", "Two of four models never traded ExxonMobil. The features had an energy ETF but no oil price; this project starts from that missing variable."],
	["NEWS", "Sentiment carried no signal, and coverage was never reported", "Its headlines came from a recent-news feed. Here: Factiva, with headline coverage reported per counter and year."],
	["MODELS", "Tree ensembles beat deep networks on average", "XGBoost was the most consistent of its four models. Plan v2 keeps the comparison and adds a linear floor."],
	["TESTING", "One 18-month test window, no intervals", "All twenty strategies trailed the index in one bull market. Here: a walk-forward record, bootstrap intervals and one lockbox."],
].forEach(([chip, head, body], i) => {
	const x = i % 2 === 0 ? 0.6 : 6.75, y = i < 2 ? 1.55 : 4.15, w = 5.95, h = 2.4;
	s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Card ${chip}` });
	s.addText(chip, { x: x + 0.3, y: y + 0.22, w: w - 0.6, h: 0.3, fontSize: 12, bold: true, charSpacing: 2, color: C.accent2, margin: 0, isTextBox: true });
	s.addText(head, { x: x + 0.3, y: y + 0.55, w: w - 0.6, h: 0.75, fontFace: "Cambria", fontSize: 19, bold: true, color: C.text1, valign: "top", margin: 0, isTextBox: true });
	s.addText(body, { x: x + 0.3, y: y + 1.32, w: w - 0.6, h: 0.95, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
});
s.addNotes("I read Kenneth Wijaya's 2026 report in full. Four lessons carry over. His energy stock was the hardest case and his features had no oil price, which is exactly where this project starts. His sentiment result is most likely a data-coverage problem, which is why Factiva and coverage reporting matter. Trees beat deep networks, so the plan keeps a linear floor. And one 18-month window is too short to judge anything, so the plan uses a walk-forward record.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
s.addText("Plan v2 keeps the aims and changes the method", { placeholder: "title" });
[
	"Machine learning becomes Aim 4: ridge, XGBoost, LSTM and TFT on one harness",
	"Fundamentals produce the ranking the brief asks for: a sector-relative F-score",
	"Jensen's alpha against the STI and commodity factors is the headline measure",
	"5- and 20-day targets, monthly rebalancing, costs from the SGX tick schedule",
	"Closing-time correction, synthetic tests, and power stated before any result",
].forEach((t, i) => numbered(s, i + 1, { x: 0.6, y: 1.6 + i * 0.95, w: 6.6, h: 0.8, text: t }));
[
	["Aim 1", "Pass-through", false], ["Aim 2", "Fundamentals and ranking", false], ["Aim 3", "News and the levy test", false],
	["Aim 4", "Model comparison (new)", true], ["Aim 5", "Strategy and validation", false],
].forEach(([a, name, hi], i) => {
	const y = 1.6 + i * 0.95;
	s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.55, y, w: 4.15, h: 0.75, rectRadius: 0.06, fill: { color: hi ? C.accent1 : C.background2 }, line: { type: "none" }, objectName: `${a} box` });
	s.addText([{ text: `${a}  `, options: { bold: true } }, { text: name }], { x: 8.8, y, w: 3.75, h: 0.75, fontSize: 15, color: hi ? C.background1 : C.text1, valign: "middle", margin: 0, isTextBox: true });
});
s.addText([{ text: "Full plan: " }, { text: PLAN_URL, options: { hyperlink: { url: PLAN_URL }, color: C.accent1 } }], { x: 0.6, y: 6.45, w: 12.1, h: 0.4, fontSize: 12, color: C.accent4, margin: 0, isTextBox: true });
s.addNotes("Plan v2 keeps the proposal's title and the pass-through-first design. The five changes on the left are the ones that matter most; the plan lists ten. The main structural change is a new Aim 4, a model comparison in the style of the 2026 project, with a linear model as the floor.");

// ======================================================================
// Section 2: findings
// ======================================================================
pres.addSection({ title: "Findings" });

const passCount = D.filter.find(f => f.threshold_sgd === 100000).counters_passing;
const passMillion = D.filter.find(f => f.threshold_sgd === 1000000).counters_passing;
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Fifteen tradable counters, costly round trips", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Round trip, % of price", labels: D.costs.labels, values: D.costs.round_trip_pct }], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, barDir: "bar", chartColors: [HEX.teal], barGapWidthPct: 45,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisLabelFormatCode: "0.0",
	valAxisMinVal: 0, valAxisMaxVal: 2.5, showLegend: false,
	showValAxisTitle: true, valAxisTitle: "Round trip, % of price: one tick plus fees with GST",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${passCount} of ${D.n_trading_core}`, label: `trading counters clear S$100k median daily value; ${passMillion} clear S$1M` });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: "0.13%", label: "fees per side with GST; crossing the spread adds one tick" });
caption(s, "Interra Resources has not traded since 31 Jan 2025. Golden Energy and Resources (delisted 2023) needs Bloomberg history. Prices as of 21 Oct 2026.");
s.addNotes("Fifteen of the seventeen counters still trading clear a S$100k median daily value; Mermaid and Union Gas fall below. Costs are the bigger issue: crossing one tick costs up to two per cent on the penny counters, which rules out daily trading and drives the monthly rebalancing in plan v2.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Same-day regressions miss half the pass-through", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
	{ name: "Same-day OLS", labels: D.timing.labels, values: D.timing.same_day },
	{ name: "Dimson: lag + same day + lead", labels: D.timing.labels, values: D.timing.dimson },
], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, barDir: "bar", barGrouping: "clustered", chartColors: [HEX.tealSoft, HEX.teal], barGapWidthPct: 40,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisLabelFormatCode: "0.0",
	valAxisMinVal: 0, showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Sensitivity to a 1% commodity move",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: pctRange(D.timing.next_day_share), label: "of the response arrives in the next SGX session; lag t-statistics up to 10" });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: "Next open", bigSize: 28, label: "signals that use an overnight commodity move trade at the next open" });
caption(s, "Commodities settle after the 17:00 SGX close: Brent in London hours, palm futures at 18:00. Palm counters omitted until Bloomberg FCPO replaces the free series.");
s.addNotes("This is the closing-time problem. Brent and gold settle after Singapore closes, so a same-day regression catches only part of the response; the rest shows up the next session. Dimson's lead-and-lag beta roughly doubles the measured sensitivity, and the result holds with Brent spot instead of futures.");

const drift = D.drift;
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Pass-through drifts over time", { placeholder: "title" });
s.addChart(pres.charts.LINE, [
	{ name: "Rolling 1-year Dimson", labels: drift.labels, values: drift.rolling },
	{ name: "Kalman, smoothed", labels: drift.labels, values: drift.kalman },
], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, chartColors: [HEX.gray2, HEX.teal], lineSize: 2, lineDataSymbol: "none",
	catAxisLabelFrequency: 24, valAxisLabelFormatCode: "0.0", valAxisMinVal: 0, showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "CNMC Goldmine: sensitivity to gold",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${D.drift.start_2014.toFixed(2)} → ${D.drift.end.toFixed(2)}`, bigSize: 30, label: "CNMC's sensitivity to gold, 2014 to now (Kalman estimate)" });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: `${D.drift.rex_min.toFixed(2)}–${D.drift.rex_max.toFixed(2)}`, bigSize: 30, label: "range of Rex International's sensitivity to Brent over the same years" });
caption(s, "A fixed beta over this decade would be wrong for both counters, and the rolling window is too noisy to use on its own. Hence the Kalman filter as the primary estimator.");
s.addNotes("The sensitivity is not constant. CNMC's response to gold roughly tripled; Rex's response to Brent swings between about 0.3 and 0.8. The Kalman filter tracks this smoothly, where a rolling window jumps around.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("The commodity is a minority of the return", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Weekly R-squared added by the commodity (points)", labels: D.weekly_r2.labels, values: D.weekly_r2.added_pp }], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, barDir: "bar", chartColors: [HEX.teal], barGapWidthPct: 45,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0",
	valAxisMinVal: 0, showLegend: false,
	showValAxisTitle: true, valAxisTitle: "Weekly R-squared added by the commodity, percentage points",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${D.basket_r2.sti_only.toFixed(2)} → ${D.basket_r2.with_commodities.toFixed(2)}`, bigSize: 30, label: "sector-basket R-squared: STI alone, then STI plus commodities" });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: "The rest", bigSize: 30, label: "is firm-specific: room for the FA, NA and TA layers" });
caption(s, "* Palm counters use the free palm series, which understates their sensitivity; Bloomberg FCPO will revise these numbers.");
s.addNotes("The proposal said a large share of each counter's return is the commodity. The data says the commodity is significant but explains a minority of weekly variance per counter. At portfolio level it matters more: adding commodity factors lifts the basket's R-squared from about 0.49 to 0.65. I would like to reframe Aim 1 this way; it is decision D6.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("The export-ban test already works", { placeholder: "title" });
s.addChart(pres.charts.BAR, D.levy.series.map(g => ({ name: g.name, labels: D.levy.events, values: g.values })), chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.teal, HEX.tealSoft, HEX.amber], barGapWidthPct: 60,
	showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0",
	showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Abnormal return, first session (%)",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${sgn(D.levy.gap_ban)} pts`, label: `Indonesian (SGX) minus Malaysian growers after the ban announcement; t = ${minus(D.levy.t_gap_ban)}` });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: `${sgn(D.levy.gap_lift)} pts`, label: `the same gap when the lifting was announced; t = ${minus(D.levy.t_gap_lift)}` });
caption(s, "Routine levy changes in July 2022 and May 2025 show no measurable effect, so severity matters. Some event dates still need checking against primary sources.");
s.addNotes("This is the natural experiment in plan v2. An export ban pushes the world price up but traps Indonesian supply at home, so Indonesian growers should lose against Malaysian ones. They did: a gap of eleven points on the first session, t of minus 5.9, and it reversed when the lifting was announced. Small levy changes show nothing, which supports severity tiers in Aim 3.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Judge on the walk-forward record, not the lockbox", { placeholder: "title" });
s.addChart(pres.charts.LINE, D.power.series.map(g => ({ name: g.name, labels: D.power.labels, values: g.values })), chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, chartColors: [HEX.gray1, HEX.teal, HEX.gray2], lineSize: 2, lineDataSymbol: "none",
	catAxisLabelFrequency: 4, valAxisLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 0.25, showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Smallest detectable IC (80% power)",
	showCatAxisTitle: true, catAxisTitle: "Months of out-of-sample data",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${D.power.lockbox_18.toFixed(2)}`, label: "smallest IC an 18-month lockbox can detect with 18 counters" });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: `${D.power.wf_120.toFixed(2)}–${D.power.wf_96.toFixed(2)}`, bigSize: 30, label: "with 8 to 10 years of walk-forward data; real signals run 0.02 to 0.05" });
caption(s, "Monthly Spearman IC, 5% two-sided. The Monte Carlo check on the next slide agrees with this formula.");
s.addNotes("With about eighteen counters, a short lockbox can only detect implausibly strong signals. So the evidence has to come from the full walk-forward record with bootstrap intervals, and the lockbox becomes a sign check. Every null result gets reported against the effect it could have detected.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("The method passes its synthetic tests", { placeholder: "title" });
const SY = D.synthetic;
[
	[`${SY.rmse_with_lag.toFixed(2)} vs ${SY.rmse_same_day.toFixed(2)}`, "Kalman error with and without the next-day term"],
	[`${Math.round(100 * SY.share_missed)}%`, "of the response missed by same-day estimation"],
	[`${SY.next_day_share_recovered.toFixed(2)}`, "next-day share recovered by Dimson betas, against 0.40 planted"],
	[`${Math.round(100 * SY.power_07_96)}%`, "power of the IC test at IC 0.07 over 96 months; the formula predicts 80%"],
	[`${(100 * SY.false_pos_min).toFixed(0)}–${(100 * SY.false_pos_max).toFixed(1)}%`, "false-positive rate of the IC test with no signal planted"],
	[`${SY.asym_detected} of ${SY.asym_runs}`, "runs that detected a planted 30% asymmetry: this test is weak"],
].forEach(([big, label], i) => {
	const col = i % 3, row = Math.floor(i / 3);
	tile(s, { x: 0.6 + col * 4.1, y: 1.55 + row * 2.15, w: 3.9, h: 1.95, big, bigSize: 30, label });
});
caption(s, "Simulated counters: drifting sensitivity, 40% next-day share, falls 30% stronger than rises, fat tails, 15% no-trade days.", 5.95);
s.addNotes("Before touching real data in earnest, the pipeline runs on simulated counters with known answers. It recovers the level and the next-day share, and the IC test behaves as the theory says. One honest weakness: the asymmetry test rarely detects a moderate asymmetry, so the plan will flag it as low-power.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("A naive sector basket earns no alpha", { placeholder: "title" });
const PL = D.plumbing;
s.addChart(pres.charts.LINE, [
	{ name: "STI total return (ES3 ETF)", labels: PL.labels, values: PL.sti },
	{ name: "Equal-weight sector basket, net of costs", labels: PL.labels, values: PL.basket },
], chartOpts({
	x: 0.6, y: 1.45, w: 8.3, h: 4.8, chartColors: [HEX.gray1, HEX.teal], lineSize: 2, lineDataSymbol: "none",
	catAxisLabelFrequency: 24, valAxisLabelFormatCode: "0", showLegend: true, legendPos: "b",
	showValAxisTitle: true, valAxisTitle: "Value of S$100 invested in January 2014",
}));
tile(s, { ...RIGHT, y: 1.55, h: 1.95, big: `${PL.sharpe_basket.toFixed(2)} vs ${PL.sharpe_sti.toFixed(2)}`, bigSize: 30, label: "Sharpe ratio: the basket net of costs against the STI total return" });
tile(s, { ...RIGHT, y: 3.75, h: 1.95, big: `${minus(PL.alpha_full)}%`, label: `Jensen's alpha a year against the STI and commodity factors; t = ${minus(PL.t_alpha_full)}` });
caption(s, "No signal is used. This run checks the cost model and the alpha regression; any strategy in Aims 4 and 5 has to clear this bar. Risk-free rate set to zero for now.");
s.addNotes("This is a plumbing run, not a strategy. An equal-weight basket of the sector, rebalanced monthly and costed tick by tick, returned 7.5 per cent a year against 8.4 for the STI, with twice the volatility and no alpha. It confirms the machinery works and sets the bar.");

// ======================================================================
// Section 3: data and decisions
// ======================================================================
pres.addSection({ title: "Data and decisions" });

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data and decisions" });
s.addText("Three gaps that free data cannot fill", { placeholder: "title" });
[
	["Daily palm oil", "The free series (CPO=F) is a monthly-average swap. First-of-month moves are 3.9 times normal, and it moved −0.7% on the ban day.", "Fix: Bloomberg FCPO"],
	["Fundamentals before 2021", "Free statements cover FY2021 to FY2025 only, with almost no quarterly data.", "Fix: Bloomberg or annual reports"],
	["Delisted counters, event times", "Golden Energy and Resources is missing, and the SGX announcements API is closed.", "Fix: Bloomberg history and Factiva"],
].forEach(([head, body, fix], i) => {
	const x = 0.6 + i * 4.1, y = 1.55, w = 3.9, h = 3.9;
	s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: C.background2 }, line: { type: "none" }, objectName: `Gap card ${i + 1}` });
	s.addText(head, { x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.8, fontFace: "Cambria", fontSize: 20, bold: true, color: C.text1, valign: "top", margin: 0, isTextBox: true });
	s.addText(body, { x: x + 0.3, y: y + 1.1, w: w - 0.6, h: 1.75, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
	s.addText(fix, { x: x + 0.3, y: y + 3.05, w: w - 0.6, h: 0.5, fontSize: 15, bold: true, color: C.accent1, valign: "top", margin: 0, isTextBox: true });
});
s.addText("Book the Business Library terminal before the 31 October decision point. The shopping list is ready.", { x: 0.6, y: 5.75, w: 12.1, h: 0.5, fontSize: 16, bold: true, color: C.accent1, margin: 0, isTextBox: true });
s.addNotes("Free data got us a long way, but three things need Bloomberg: a real daily palm-oil futures series, fundamentals before 2021, and the delisted Golden Energy counter. I have a shopping list of tickers and fields ready for a terminal session this week.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data and decisions" });
s.addText("Eight decisions to settle today", { placeholder: "title" });
const decisions = [
	["D1 · Commodity data", "Bloomberg FCPO, coal and freight; free monthly data as the fallback"],
	["D2 · Universe", "S$100k median daily value, point-in-time: 15 counters today"],
	["D3 · Horizons", "5- and 20-day targets; monthly rebalancing; next-open execution"],
	["D4 · Machine learning", "Four models as in Wijaya (2026); the TFT is dropped first if time runs short"],
	["D5 · Fundamentals", "Sector-relative F-score ranking, plus the pass-through panel"],
	["D6 · Aim 1 framing", "Significant, drifting, partly next-day, but a minority of the variance"],
	["D7 · News", "Residual event studies with severity tiers; the levy test as the headline"],
	["D8 · Validation", "Walk-forward record with intervals; the lockbox as a sign check"],
];
const head = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.accent1 } } });
const rows = [[head("Decision"), head("Recommendation")]].concat(decisions.map(([d, r], i) => [
	{ text: d, options: { bold: true, color: C.text1, fill: { color: i % 2 ? C.background1 : C.background2 } } },
	{ text: r, options: { color: C.text1, fill: { color: i % 2 ? C.background1 : C.background2 } } },
]));
s.addTable(rows, { x: 0.6, y: 1.45, w: 12.1, colW: [3.3, 8.8], fontSize: 14, rowH: 0.52, valign: "middle", margin: [0.04, 0.15, 0.04, 0.15], border: { type: "solid", pt: 0.75, color: HEX.border } });
caption(s, "Each decision, with its options and evidence, is in consultation/decision_brief.md.", 6.35);
s.addNotes("These are the eight decisions in the brief. Most are recommendations I am confident in; the ones I most need your view on are D4, the size of the machine-learning stage, and D5, whether the sector-relative F-score works as the stage 01 ranking.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data and decisions" });
s.addText("Questions for Prof. Wong", { placeholder: "title" });
[
	"Which title was registered on Stafflink before 5 October?",
	"The interim report: its date, length and format, and what the video must cover?",
	"Is a sector-relative F-score acceptable as the stage 01 ranking method?",
	"Four models, as in Wijaya (2026), or ridge and XGBoost only?",
	"May Wijaya (2026) be cited as prior work in this group?",
	"Does EEE require a declaration on the use of generative AI tools?",
	"Any advice on Bloomberg access, or data from earlier students?",
].forEach((q, i) => numbered(s, i + 1, { x: 0.6, y: 1.55 + i * 0.68, w: 11.4, h: 0.5, text: q, fontSize: 18 }));
s.addNotes("Seven questions, in order of how much they change the next three weeks. The first two are administrative but urgent.");

s = pres.addSlide({ masterName: "CLOSING", sectionTitle: "Data and decisions" });
s.addText("Next three weeks, to the interim report", { placeholder: "title" });
[
	["S1 W10 · this week", "Data", ["Bloomberg session from the shopping list", "Factiva test export", "Commodity data decision by 31 October"]],
	["S1 W11", "Aim 1", ["Rerun pass-through with Bloomberg FCPO", "Freeze the harness and seal the lockbox", "Write up the synthetic tests"]],
	["S1 W12 to W13", "Interim report", ["Chapters 1 to 4", "The interim video"]],
].forEach(([when, headText, items], i) => {
	const x = 0.6 + i * 4.2, w = 3.7;
	s.addText(when, { x, y: 1.9, w, h: 0.4, fontSize: 14, bold: true, color: C.accent5, margin: 0, isTextBox: true });
	s.addText(headText, { x, y: 2.35, w, h: 0.7, fontFace: "Cambria", fontSize: 26, bold: true, color: C.background1, margin: 0, isTextBox: true });
	s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
		{ x, y: 3.2, w, h: 2.6, fontSize: 16, color: C.background1, valign: "top", paraSpaceAfter: 8, margin: 0, isTextBox: true });
	if (i < 2) s.addShape(pres.shapes.LINE, { x: x + w + 0.1, y: 2.7, w: 0.3, h: 0, line: { color: C.accent5, width: 2, endArrowType: "triangle" } });
});
s.addText([{ text: "Materials: " }, { text: "plan v2", options: { hyperlink: { url: PLAN_URL } } }, { text: " · consultation/decision_brief.md · pipeline in ~/Desktop/FYP/fyp-pipeline" }],
	{ x: 0.6, y: 6.25, w: 12.1, h: 0.4, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true });
s.addNotes("If the decisions land today, the next three weeks are data, then Aim 1 on Bloomberg data, then the interim report and video.");

(async () => {
	await pres.writeFile({ fileName: OUT });
	const { applyTheme } = require(SKILL_THEME);
	await applyTheme(OUT, THEME);
	console.log("wrote", OUT);
})();
