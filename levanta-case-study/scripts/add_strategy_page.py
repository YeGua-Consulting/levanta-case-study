#!/usr/bin/env python3
"""Insert a '站外媒体组合' strategy page (table: 媒体类型 / 适合做的内容 / 主要作用 / 媒体举例) at a given position.

Usage: python3 add_strategy_page.py <in.pptx> <out.pptx> <strategy.json> [--after N]
  --after N  insert after slide N (1-based; default: after the last fixed media page, i.e. before the hook page = after 5)
The page follows the case template's visual language (F5F8F6 background, 0C2B1C header band, 168447 accent,
Arial Unicode MS) and renumbers every page to "0N / 0T". Content is fully config-driven so the same module serves
any category: copy assets/strategy-page-default.json next to the case and replace the 〔…〕 placeholders.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

EMU_PER_PX = 12192000 / 1280
FONT = "Arial Unicode MS"
C_BG, C_TEXT, C_DARK, C_ACCENT, C_LIGHT, C_LINE, C_MUTED, C_BODY = (
    "F5F8F6", "14231B", "0C2B1C", "168447", "E8F4ED", "DDE5DF", "5C6B62", "2E3B34")
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def px(v):
    return Emu(int(round(v * EMU_PER_PX)))


def rgb(h):
    return RGBColor.from_string(h)


def add_text(slide, name, x, y, w, h, paras, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margins=(0, 0, 0, 0), line_spacing=None):
    """paras: list of paragraphs; each paragraph is a list of (text, size_pt, color_hex, bold)."""
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (px(m) for m in margins)
    tf.vertical_anchor = anchor
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        for text, size, color, bold in para:
            r = p.add_run()
            r.text = text
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = rgb(color)
            rPr = r._r.get_or_add_rPr()
            for tag in ("ea", "cs"):
                el = rPr.find("{%s}%s" % (A_NS, tag))
                if el is None:
                    el = rPr.makeelement("{%s}%s" % (A_NS, tag), {})
                    rPr.append(el)
                el.set("typeface", FONT)
    return tb


def add_rect(slide, name, x, y, w, h, fill_hex, line_hex=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    shp.name = name
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill_hex)
    if line_hex:
        shp.line.color.rgb = rgb(line_hex)
        shp.line.width = Pt(0.75)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def add_line(slide, name, x, y, w, color_hex):
    ln = slide.shapes.add_connector(1, px(x), px(y), px(x + w), px(y))
    ln.name = name
    ln.line.color.rgb = rgb(color_hex)
    ln.line.width = Pt(0.75)
    return ln


def main(src, dst, cfg_path, after=None):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    prs = Presentation(src)
    n_before = len(prs.slides)
    after = cfg.get("insert_after", 5) if after is None else after
    layout = prs.slides[n_before - 1].slide_layout
    slide = prs.slides.add_slide(layout)
    sldIdLst = prs.slides._sldIdLst
    new_id = sldIdLst[-1]
    sldIdLst.remove(new_id)
    sldIdLst.insert(after, new_id)
    total = len(prs.slides)
    pos = after + 1

    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(C_BG)

    # header
    add_text(slide, "Section eyebrow", 52.8, 36, 1000, 22, [[(cfg["eyebrow"], 11, C_ACCENT, True)]])
    add_text(slide, "Slide title", 52.8, 64, 1174.4, 48, [[(cfg["title"], 26, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Subtitle", 52.8, 120, 1174.4, 26, [[(cfg["subtitle"], 11, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)

    # table geometry
    x0, y0, W = 52.8, 160, 1174.4
    col_w = cfg.get("col_widths", [236, 300, 290, 348.4])
    assert abs(sum(col_w) - W) < 1, "col_widths must sum to 1174.4"
    xs = [x0]
    for w_ in col_w[:-1]:
        xs.append(xs[-1] + w_)
    head_h = cfg.get("header_height", 34)
    row_h = cfg.get("row_height", 64)
    pad = 10

    # header row
    add_rect(slide, "Table header", x0, y0, W, head_h, C_DARK)
    for ci, (hx, hw, label) in enumerate(zip(xs, col_w, cfg["columns"])):
        add_text(slide, f"Header {ci}", hx, y0, hw, head_h, [[(label, 11, "FFFFFF", True)]],
                 anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 0, pad, 0))

    # body rows
    y = y0 + head_h
    for ri, row in enumerate(cfg["rows"]):
        fill = "FFFFFF" if ri % 2 == 0 else C_BG
        add_rect(slide, f"Row {ri+1} bg", x0, y, W, row_h, fill)
        add_rect(slide, f"Row {ri+1} type bg", x0, y, col_w[0], row_h, C_LIGHT)
        type_paras = [[(row["type"], 11.5, C_TEXT, True)]]
        if row.get("type_sub"):
            type_paras.append([(row["type_sub"], 9, C_MUTED, False)])
        add_text(slide, f"Row {ri+1} type", xs[0], y, col_w[0], row_h, type_paras, anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 4, pad, 4))
        for ci, key in enumerate(("content", "role", "examples"), start=1):
            val = row[key]
            lines = val if isinstance(val, list) else [val]  # a list forces line breaks between items
            add_text(slide, f"Row {ri+1} {key}", xs[ci], y, col_w[ci], row_h, [[(t, 10.5, C_BODY, False)] for t in lines],
                     anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 4, pad, 4))
        add_line(slide, f"Row {ri+1} divider", x0, y + row_h, W, C_LINE)
        y += row_h

    # bottom band (positioning only; demo CTA lives on the hook/contact pages)
    if cfg.get("band"):
        band_y = y + 16
        band_h = cfg.get("band_height", 44)
        add_rect(slide, "Positioning band", x0, band_y, W, band_h, C_DARK)
        add_text(slide, "Band text", x0 + 20, band_y, W - 40, band_h, [[(cfg["band"], 12, "FFFFFF", True)]],
                 anchor=MSO_ANCHOR.MIDDLE)

    if cfg.get("footer"):
        add_text(slide, "Source footer", 52.8, 690, 1050, 17, [[(cfg["footer"], 7.5, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Page number", 1162, 690, 65, 17, [[(f"{pos:02d} / {total:02d}", 8, C_MUTED, False)]],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    slide.notes_slide.notes_text_frame.text = cfg.get("notes", "")

    # renumber all other pages
    pat = re.compile(r"^(0\d) / 0\d$")
    for idx, s in enumerate(prs.slides, start=1):
        if s is slide:
            continue
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            if pat.match(sh.text_frame.text.strip()):
                for p in sh.text_frame.paragraphs:
                    runs = p.runs
                    if runs:
                        runs[0].text = f"{idx:02d} / {total:02d}"
                        for r in runs[1:]:
                            r.text = ""
    prs.save(dst)
    print(f"saved {dst}: {total} slides; strategy page at position {pos}")


if __name__ == "__main__":
    args = sys.argv[1:]
    after = None
    if "--after" in args:
        i = args.index("--after")
        after = int(args[i + 1])
        del args[i:i + 2]
    main(args[0], args[1], args[2], after)
