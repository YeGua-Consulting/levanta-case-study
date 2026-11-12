#!/usr/bin/env python3
"""Insert a '出单伙伴结构 × 客户覆盖现状' page: platform partner-type shares (bar chart, left) next to a
coverage/opportunity table for one target client (right), plus a takeaway band. For 定向版 decks.

Usage: python3 add_structure_page.py <in.pptx> <out.pptx> <structure.json> [--after N]

structure.json
{
  "insert_after": 5,
  "eyebrow": "为 ×× 准备 · 出单伙伴结构与覆盖现状",
  "title": "…", "subtitle": "…",
  "chart": {"title": "Levanta 全网近 12 个月前 100 伙伴的销售额占比",
            "bars": [{"label": "内容型伙伴（媒体＋创作者）", "value": 53, "highlight": true, "value_label": "一半以上"}, …],
            # value drives the bar length; value_label (optional) replaces the printed "53%" — use it when the
            # figure is an internal analysis that should be shown rounded ("约三成") rather than as an exact statistic
            "note": "来源：…"},
  "table": {"columns": ["伙伴类型", "客户现状", "机会点"], "col_widths": [150, 240, 237],
            "rows": [{"type": "内容型 · 创作者", "status": "✓ 已有", "status_kind": "yes|no|none",
                      "now": "…", "next": "…"}, …]},
  "band": "一句话结论",
  "footer": "来源与边界", "notes": "演讲者备注"
}
Visual language and renumbering follow add_strategy_page.py. Only aggregate / public data belongs on this page:
platform shares from Levanta's own published material, client status from public pages — never another brand's
backend data.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_strategy_page import add_line, add_rect, add_text, rgb, C_BG, C_TEXT, C_DARK, C_ACCENT, C_LIGHT, C_LINE, C_MUTED, C_BODY  # noqa: E402

STATUS_COLOR = {"yes": "168447", "no": "B3261E", "none": "5C6B62", "partial": "C27C0E"}


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

    add_text(slide, "Section eyebrow", 52.8, 36, 1000, 22, [[(cfg["eyebrow"], 11, C_ACCENT, True)]])
    add_text(slide, "Slide title", 52.8, 64, 1174.4, 48, [[(cfg["title"], 26, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Subtitle", 52.8, 120, 1174.4, 26, [[(cfg["subtitle"], 11, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------------- left: bar chart
    ch = cfg["chart"]
    cx, cy, cw = 52.8, 160, cfg.get("chart_width", 500)
    add_rect(slide, "Chart panel", cx, cy, cw, 350, "FFFFFF", C_LINE)
    add_text(slide, "Chart title", cx + 18, cy + 12, cw - 36, 24, [[(ch["title"], 11.5, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
    bars = ch["bars"]
    label_w, val_w, gap = 170, cfg.get("chart", {}).get("value_width", 52), 12
    track_x = cx + 18 + label_w + gap
    track_w = cw - 36 - label_w - gap - val_w - gap
    n = len(bars)
    area_top, area_h = cy + 52, 350 - 52 - 58
    slot = area_h / n
    bar_h = min(34, slot * 0.6)
    vmax = max(float(b["value"]) for b in bars) or 1
    for i, b in enumerate(bars):
        by = area_top + i * slot + (slot - bar_h) / 2
        add_text(slide, f"Bar label {i}", cx + 18, by - 6, label_w, bar_h + 12, [[(b["label"], 10.5, C_TEXT, True)]],
                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        add_rect(slide, f"Bar track {i}", track_x, by, track_w, bar_h, C_LIGHT)
        fill_w = max(2, track_w * float(b["value"]) / vmax)
        add_rect(slide, f"Bar fill {i}", track_x, by, fill_w, bar_h, C_DARK if b.get("highlight") else C_ACCENT)
        add_text(slide, f"Bar value {i}", track_x + track_w + gap, by - 6, val_w, bar_h + 12,
                 [[(b.get("value_label", f"{b['value']}%"), 12, C_TEXT, True)]], anchor=MSO_ANCHOR.MIDDLE)
    if ch.get("note"):
        add_text(slide, "Chart note", cx + 18, cy + 350 - 50, cw - 36, 40, [[(ch["note"], 8, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------------- right: coverage table
    tb = cfg["table"]
    tx = cx + cw + 20
    tw = 1174.4 - cw - 20
    col_w = tb.get("col_widths", [150, 250, tw - 400])
    assert abs(sum(col_w) - tw) < 1, f"table col_widths must sum to {tw}"
    xs = [tx]
    for w_ in col_w[:-1]:
        xs.append(xs[-1] + w_)
    head_h = 34
    rows = tb["rows"]
    row_h = (350 - head_h) / len(rows)
    pad = 10
    add_rect(slide, "Table header", tx, cy, tw, head_h, C_DARK)
    for ci, (hx, hw, label) in enumerate(zip(xs, col_w, tb["columns"])):
        add_text(slide, f"Header {ci}", hx, cy, hw, head_h, [[(label, 11, "FFFFFF", True)]],
                 anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 0, pad, 0))
    y = cy + head_h
    for ri, row in enumerate(rows):
        add_rect(slide, f"Row {ri+1} bg", tx, y, tw, row_h, "FFFFFF" if ri % 2 == 0 else C_BG)
        add_rect(slide, f"Row {ri+1} type bg", tx, y, col_w[0], row_h, C_LIGHT)
        add_text(slide, f"Row {ri+1} type", xs[0], y, col_w[0], row_h, [[(row["type"], 10.5, C_TEXT, True)]],
                 anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 4, pad, 4))
        status_color = STATUS_COLOR.get(row.get("status_kind", "none"), C_MUTED)
        now_lines = row["now"] if isinstance(row["now"], list) else [row["now"]]
        paras = [[(row.get("status", ""), 10.5, status_color, True)]] + [[(t, 9.5, C_BODY, False)] for t in now_lines]
        add_text(slide, f"Row {ri+1} now", xs[1], y, col_w[1], row_h, paras, anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 4, pad, 4))
        next_lines = row["next"] if isinstance(row["next"], list) else [row["next"]]
        add_text(slide, f"Row {ri+1} next", xs[2], y, col_w[2], row_h, [[(t, 9.5, C_BODY, False)] for t in next_lines],
                 anchor=MSO_ANCHOR.MIDDLE, margins=(pad, 4, pad, 4))
        add_line(slide, f"Row {ri+1} divider", tx, y + row_h, tw, C_LINE)
        y += row_h

    # ---------------------------------------------------------------- band + footer + page number
    if cfg.get("band"):
        band_y = cy + 350 + 16
        band_h = cfg.get("band_height", 50)
        add_rect(slide, "Takeaway band", 52.8, band_y, 1174.4, band_h, C_DARK)
        add_text(slide, "Band text", 72.8, band_y, 1134.4, band_h, [[(cfg["band"], 12, "FFFFFF", True)]], anchor=MSO_ANCHOR.MIDDLE)
    if cfg.get("footer"):
        add_text(slide, "Source footer", 52.8, 686, 1050, 24, [[(cfg["footer"], 7.5, C_MUTED, False)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, "Page number", 1162, 690, 65, 17, [[(f"{pos:02d} / {total:02d}", 8, C_MUTED, False)]],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    slide.notes_slide.notes_text_frame.text = cfg.get("notes", "")

    pat = re.compile(r"^(0\d) / 0\d$")
    for idx, s in enumerate(prs.slides, start=1):
        if s is slide:
            continue
        for sh in s.shapes:
            if sh.has_text_frame and pat.match(sh.text_frame.text.strip()):
                for p in sh.text_frame.paragraphs:
                    runs = p.runs
                    if runs:
                        runs[0].text = f"{idx:02d} / {total:02d}"
                        for r in runs[1:]:
                            r.text = ""
    prs.save(dst)
    print(f"saved {dst}: {total} slides; structure page at position {pos}")


if __name__ == "__main__":
    args = sys.argv[1:]
    after = None
    if "--after" in args:
        i = args.index("--after")
        after = int(args[i + 1])
        del args[i:i + 2]
    main(args[0], args[1], args[2], after)
