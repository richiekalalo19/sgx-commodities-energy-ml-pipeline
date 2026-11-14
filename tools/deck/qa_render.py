"""Layout QA for the deck without LibreOffice: measures every text box with the real Calibri and Cambria
fonts, flags overflow, overlaps and edge crowding, and draws a preview PNG per slide.

The preview is a wireframe: shapes, fills and wrapped text are drawn to scale; charts are grey panels.
Run:  .venv/bin/python -I tools/deck/qa_render.py consultation/deck_draft.pptx consultation/qa
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu

FONT_DIR = Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts")
FONTS = {("Calibri", False): "Calibri.ttf", ("Calibri", True): "Calibrib.ttf",
         ("Cambria", False): "Cambria.ttc", ("Cambria", True): "Cambriab.ttf"}
THEME = {"dk1": "0E1A18", "lt1": "FFFFFF", "dk2": "0B4F47", "lt2": "EEF3F1", "accent1": "0B5F55",
         "accent2": "A85B16", "accent3": "3E9D8D", "accent4": "5B6B67", "accent5": "8AC4B4", "accent6": "E3B65C",
         "tx1": "0E1A18", "bg1": "FFFFFF", "tx2": "0B4F47", "bg2": "EEF3F1"}
# Placeholder defaults from the layouts in build_deck.js: (font, size, bold)
PH = {("TITLE", "title"): ("Cambria", 40, True), ("TITLE", "subtitle"): ("Calibri", 20, False),
      ("TITLE", "meta"): ("Calibri", 14, False), ("CONTENT", "title"): ("Cambria", 36, True),
      ("CLOSING", "title"): ("Cambria", 36, True)}
PX = 100  # pixels per inch
EMU_IN = 914400


def font(face: str, bold: bool, size_pt: float):
    face = "Cambria" if "Cambria" in (face or "") else "Calibri"
    return ImageFont.truetype(str(FONT_DIR / FONTS[(face, bold)]), max(1, int(round(size_pt * PX / 72))))


def wrap(text: str, f, width_px: float) -> list[str]:
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(" "), ""
        for w in words:
            trial = (cur + " " + w).strip()
            if f.getlength(trial) <= width_px or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def resolve(fc) -> str | None:
    """Hex string for a python-pptx ColorFormat (theme or rgb), or None."""
    try:
        if fc is None or fc.type is None:
            return None
        if getattr(fc, "theme_color", None) is not None:
            name = str(fc.theme_color).split(".")[-1].split(" ")[0].lower()
            key = {"accent_1": "accent1", "accent_2": "accent2", "accent_3": "accent3", "accent_4": "accent4",
                   "accent_5": "accent5", "accent_6": "accent6", "text_1": "tx1", "text_2": "tx2",
                   "background_1": "bg1", "background_2": "bg2"}.get(name, name)
            return THEME.get(key)
        return str(fc.rgb)
    except Exception:
        return None


def color_of(fill) -> str | None:
    try:
        if fill.type is None:
            return None
        fc = fill.fore_color
        if fc.type is not None and getattr(fc, "theme_color", None) is not None:
            name = str(fc.theme_color).split(".")[-1].split(" ")[0].lower()
            key = {"accent_1": "accent1", "accent_2": "accent2", "accent_3": "accent3", "accent_4": "accent4",
                   "accent_5": "accent5", "accent_6": "accent6", "text_1": "tx1", "text_2": "tx2",
                   "background_1": "bg1", "background_2": "bg2"}.get(name, name)
            return THEME.get(key)
        return str(fc.rgb)
    except Exception:
        return None


def runs_info(shape, layout_name):
    """(text, face, size, bold) for the text frame, resolving placeholder defaults."""
    tf = shape.text_frame
    text = "\n".join(p.text for p in tf.paragraphs)
    face, size, bold = "Calibri", 18, False
    if shape.is_placeholder:
        key = (layout_name, shape.name.split(" ")[0].lower() if shape.name else "")
        name = shape.placeholder_format.type
        for (lay, ph), val in PH.items():
            if lay == layout_name and ph in (shape.name or "").lower():
                face, size, bold = val
    for p in tf.paragraphs:
        for r in p.runs:
            if r.font.size:
                size = r.font.size.pt
            if r.font.name:
                face = r.font.name
            if r.font.bold is not None:
                bold = r.font.bold
            break
        break
    return text, face, size, bold


def main(deck: str, outdir: str):
    prs = Presentation(deck)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    W, H = prs.slide_width / EMU_IN, prs.slide_height / EMU_IN
    problems = []
    for idx, slide in enumerate(prs.slides, 1):
        layout = slide.slide_layout.name
        bg = "0B4F47" if layout in ("TITLE", "CLOSING") else "FFFFFF"
        img = Image.new("RGB", (int(W * PX), int(H * PX)), "#" + bg)
        d = ImageDraw.Draw(img)
        boxes = []
        for shp in slide.shapes:
            x, y = shp.left / EMU_IN, shp.top / EMU_IN
            w, h = shp.width / EMU_IN, shp.height / EMU_IN
            rect = [x * PX, y * PX, (x + w) * PX, (y + h) * PX]
            if shp.has_chart if hasattr(shp, "has_chart") else False:
                d.rectangle(rect, fill="#E9EEEC", outline="#B9C4C0")
                d.text((rect[0] + 8, rect[1] + 8), f"chart: {shp.chart.chart_type}", fill="#5B6B67", font=font("Calibri", False, 11))
                boxes.append((shp.name, x, y, w, h, "chart"))
                continue
            if shp.has_table if hasattr(shp, "has_table") else False:
                tbl = shp.table
                cy = y
                for r_i, row in enumerate(tbl.rows):
                    rh = row.height / EMU_IN
                    cx = x
                    for c_i, cell in enumerate(row.cells):
                        cw = tbl.columns[c_i].width / EMU_IN
                        cf = color_of(cell.fill)
                        fill = "#" + cf if cf else ("#0B5F55" if r_i == 0 else ("#EEF3F1" if r_i % 2 == 1 else "#FFFFFF"))
                        d.rectangle([cx * PX, cy * PX, (cx + cw) * PX, (cy + rh) * PX], fill=fill, outline="#D6DEDB")
                        f = font("Calibri", r_i == 0 or c_i == 0, 14)
                        lines = wrap(cell.text, f, (cw - 0.30) * PX)
                        need = len(lines) * 14 * 1.2 / 72 + 0.08
                        if need > rh + 0.01:
                            problems.append(f"slide {idx}: table cell r{r_i}c{c_i} needs {need:.2f} in, row is {rh:.2f} in")
                        for k, ln in enumerate(lines):
                            d.text(((cx + 0.15) * PX, (cy + 0.06) * PX + k * 14 * 1.2 * PX / 72), ln,
                                   fill="#FFFFFF" if r_i == 0 else "#0E1A18", font=f)  # header white, body ink
                        cx += cw
                    cy += rh
                boxes.append((shp.name, x, y, w, cy - y, "table"))
                continue
            fill = color_of(shp.fill) if hasattr(shp, "fill") else None
            if fill:
                d.rounded_rectangle(rect, radius=6, fill="#" + fill)
            if getattr(shp, "has_text_frame", False) and shp.has_text_frame and shp.text_frame.text.strip():
                text, face, size, bold = runs_info(shp, layout)
                tf = shp.text_frame
                ml = (tf.margin_left if tf.margin_left is not None else Emu(91440)) / EMU_IN
                mr = (tf.margin_right if tf.margin_right is not None else Emu(91440)) / EMU_IN
                mt = (tf.margin_top if tf.margin_top is not None else Emu(45720)) / EMU_IN
                mb = (tf.margin_bottom if tf.margin_bottom is not None else Emu(45720)) / EMU_IN
                f = font(face, bool(bold), size)
                lines = wrap(text, f, (w - ml - mr) * PX)
                need = len(lines) * size * 1.2 / 72 + mt + mb
                widest = max((f.getlength(wd) for wd in text.split()), default=0) / PX
                if need > h + 0.02:
                    problems.append(f"slide {idx}: '{text[:50]}' needs {need:.2f} in, box is {h:.2f} in ({len(lines)} lines at {size}pt)")
                if widest > (w - ml - mr) + 0.01:
                    problems.append(f"slide {idx}: a word in '{text[:40]}' is wider than its box")
                if x < 0.45 or x + w > W - 0.45 or y < 0.3 or y + h > H - 0.15:
                    problems.append(f"slide {idx}: '{text[:40]}' sits within 0.45 in of the slide edge")
                run_color = None
                for para in tf.paragraphs:
                    for run in para.runs:
                        run_color = resolve(run.font.color)
                        break
                    break
                ink = "#" + run_color if run_color else ("#FFFFFF" if bg != "FFFFFF" and not fill else "#0E1A18")
                for k, ln in enumerate(lines):
                    d.text(((x + ml) * PX, (y + mt) * PX + k * size * 1.2 * PX / 72), ln, fill=ink, font=f)
                boxes.append((shp.name, x, y, w, min(h, need), "text"))
        # overlaps between text boxes (not text over its own card)
        texts = [b for b in boxes if b[5] in ("text", "chart", "table")]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                ox = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
                oy = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
                if ox > 0.02 and oy > 0.02:
                    problems.append(f"slide {idx}: '{a[0]}' overlaps '{b[0]}' by {ox:.2f} x {oy:.2f} in")
        img.save(out / f"slide-{idx:02d}.png")
    print("\n".join(problems) if problems else "No overflow, overlap or edge problems found.")
    print(f"Previews: {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
