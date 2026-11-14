#!/bin/bash
# Rebuilds every dataset, table and figure from scratch. About five minutes on a laptop.
# Usage:  ./run_all.sh            (download fresh data, then analyse)
#         ./run_all.sh --offline  (reuse the latest raw downloads)
set -e
cd "$(dirname "$0")"
PY=".venv/bin/python -I"
mkdir -p logs
if [ "$1" != "--offline" ]; then
  $PY scripts/01_collect_market_data.py   > logs/01_collect.log 2>&1
  $PY scripts/03_probe_fundamentals.py    > logs/03_fundamentals.log 2>&1 || echo "fundamentals probe failed (network?)"
fi
$PY scripts/02_build_panel.py             > logs/02_panel.log 2>&1
# Point-in-time fundamentals (needs the panel for prices): downloads statements, or reuses the latest with --offline
if [ "$1" != "--offline" ]; then
  $PY scripts/04_fundamentals_pit.py      > logs/04_fundamentals_pit.log 2>&1 || echo "fundamentals download failed (network?)"
else
  $PY scripts/04_fundamentals_pit.py --offline > logs/04_fundamentals_pit.log 2>&1
fi
$PY scripts/10_liquidity_costs.py         > logs/10_liquidity.log 2>&1
$PY scripts/11_passthrough_timing.py      > logs/11_passthrough.log 2>&1
$PY scripts/12_synthetic_validation.py    > logs/12_synthetic.log 2>&1
$PY scripts/13_levy_event_study.py        > logs/13_levy.log 2>&1
$PY scripts/14_basket_plumbing.py         > logs/14_plumbing.log 2>&1
$PY scripts/15_residuals_all.py           > logs/15_residuals.log 2>&1
$PY scripts/16_harness.py                 > logs/16_harness.log 2>&1   # refuses to rebuild once the lockbox is opened
echo "Done. Tables in reports/tables, figures in reports/figures, logs in logs/."
# Consultation pack: deck data, slide draft, web brief
$PY scripts/20_deck_data.py               > logs/20_deck_data.log 2>&1
NODE_PATH=tools/deck/node_modules node tools/deck/build_deck.js > logs/20_deck.log 2>&1
$PY scripts/21_brief_html.py              > logs/21_brief.log 2>&1
echo "Pack rebuilt: consultation/deck_draft.pptx and consultation/brief.html"
# Interim progress deck
$PY scripts/22_progress_data.py           > logs/22_progress.log 2>&1
NODE_PATH=tools/deck/node_modules node tools/deck/build_progress_deck.js > logs/22_deck.log 2>&1
echo "Interim deck rebuilt: interim/FYP_Interim_Progress.pptx"
