#!/usr/bin/env python3
"""Insert a '卖家常见问题 + 定位 + 演示邀请' hook page before the contact page.

Usage: python3 add_questions_page.py <in.pptx> <out.pptx> <questions.json>
The page follows the case template's visual language (F5F8F6 background, 0C2B1C band,
168447 accent, Arial Unicode MS) and renumbers every page to "0N / 0T".
"""
from __future__ import annotations

import copy
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
C_BG, C_TEXT, C_DARK, C_ACCENT, C_LIGHT, C_LINE, C_MUTED = (
    "F5F8F6", "14231B", "0C2B1C", "168447", "E8F4ED", "DDE5DF", "5C6B62")


def px(v):
    return Emu(int(round(v * EMU_PER_PX)))


def rgb(h):
    return RGBColor.from_string(h)


def add_text(slide, name, x, y, w, h, runs, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=None):
    """runs: list of paragraphs; each paragraph is a list of (text, size_pt, color_hex, bold)."""
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
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
            # CJK / complex-script font faces
            rPr = r._r.get_or_add_rPr()
            for tag in ("ea", "cs"):
                el = rPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}%s" % tag)
                if el is None:
                    el = rPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}%s" % tag, {})
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
    ln = slide.shapes.add_connector(1, px(x), px(y), px(x + w), px(y))  # straight
    ln.name = name
    ln.line.color.rgb = rgb(color_hex)
    ln.line.width = Pt(0.75)
    return ln


def main(src, dst, cfg_path):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    prs = Presentation(src)
    n_before = len(prs.slides)
    contact = prs.slides[n_before - 1]
    layout = contact.slide_layout
    slide = prs.slides.add_slide(layout)
    # move the new slide before the contact page
    sldIdLst = prs.slides._sldIdLst
    new_id = sldIdLst[-1]
    sldIdLst.remove(new_id)
    sldIdLst.insert(n_before - 1, new_id)
    total = len(prs.slides)

    # background to match the template
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(C_BG)

    # header
    add_text(slide, "Section eyebrow", 52.8, 36, 1000, 22, [[(cfg["eyebrow"], 11, C_ACCENT, True)]])
    add_text(slide, "Slide title", 52.8, 64, 1174.4, 48, [[(cfg["title"], 26, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Subtitle", 52.8, 120, 1174.4, 26, [[(cfg["subtitle"], 11, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)

    # question rows
    rows = cfg["questions"]
    y0, row_h = 160, cfg.get("row_height", 62)
    for i, q in enumerate(rows):
        y = y0 + i * row_h
        add_text(slide, f"Q{i+1} number", 52.8, y, 40, row_h, [[(f"{i+1:02d}", 12, C_ACCENT, True)]], anchor=MSO_ANCHOR.MIDDLE)
        add_text(slide, f"Q{i+1} label", 100, y, 190, row_h, [[(q["label"], 13.5, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
        add_text(slide, f"Q{i+1} text", 300, y, 927, row_h, [[(q["text"], 12.5, "2E3B34", False)]], anchor=MSO_ANCHOR.MIDDLE)
        if i < len(rows) - 1:
            add_line(slide, f"Q{i+1} divider", 52.8, y + row_h, 1174.4, C_LINE)

    # dark band: root cause + positioning + CTA
    band_y = y0 + len(rows) * row_h + 18
    band_h = cfg.get("band_height", 100)
    add_rect(slide, "Positioning band", 52.8, band_y, 1174.4, band_h, C_DARK)
    add_text(slide, "Root cause", 73, band_y + 12, 1130, 26,
             [[(cfg["root_cause"], 13, "FFFFFF", True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Positioning", 73, band_y + 42, 1130, 22,
             [[(cfg["positioning"], 11, "BFE3CC", False)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Pillars", 73, band_y + 66, 760, 20,
             [[(cfg["pillars"], 10, "8FC7A5", False)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Demo CTA", 820, band_y + 60, 383, 30,
             [[(cfg["cta"], 12, "FFFFFF", True)]], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

    if cfg.get("footer"):
        add_text(slide, "Source footer", 52.8, 690, 1050, 17, [[(cfg["footer"], 7.5, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Page number", 1162, 690, 65, 17, [[(f"{total-1:02d} / {total:02d}", 8, C_MUTED, False)]],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

    # notes
    slide.notes_slide.notes_text_frame.text = cfg.get("notes", "")

    # renumber all other pages
    pat = re.compile(r"^(0\d) / 0\d$")
    for idx, s in enumerate(prs.slides, start=1):
        if s is slide:
            continue
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            txt = sh.text_frame.text.strip()
            if pat.match(txt):
                for p in sh.text_frame.paragraphs:
                    runs = p.runs
                    if runs:
                        runs[0].text = f"{idx:02d} / {total:02d}"
                        for r in runs[1:]:
                            r.text = ""
    prs.save(dst)
    print(f"saved {dst}: {total} slides; hook page at position {total-1}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
