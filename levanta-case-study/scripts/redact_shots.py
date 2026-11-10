#!/usr/bin/env python3
"""Redact Levanta backend screenshots for external decks (data-compliance).

What gets masked (pixelated or whited out), keeping the page recognisable as a Levanta report:
  * the KPI card row numbers (点击量 / 转化量 / 销售额 / 佣金 / BRB / ROAS …) — labels stay, values are pixelated
  * in a 创作者报告: every creator/publisher name + avatar on the left, and the amount label after each bar;
    the bars themselves stay, so the "many partner types are selling" shape is still visible
Detection is based on the Levanta UI colours (card grey #E9E9E9, orange / purple bars), so it works on both the
Chinese and English UI and on any crop that still contains the KPI cards.

    python3 redact_shots.py <in.png> <out.png>            # one file
    from redact_shots import redact; log = redact(src, dst)

Original bytes are never modified; the redacted copy is a new PNG. `redact()` returns a dict describing the regions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

CARD_GREY = (226, 240)        # Levanta KPI card background (~233)
BAR_MIN_PIXELS = 3            # per image row, to count as part of a bar (short bars can be 4 px wide)
NAME_COL_WIDTH = 240          # px to the left of the bars that hold avatar + name
AMOUNT_LABEL_WIDTH = 200      # px after the bar end that hold the "US$12,345.67" label


def _runs(idx):
    """Group a sorted index array into (start, end) runs of consecutive values."""
    out = []
    if len(idx) == 0:
        return out
    s = p = int(idx[0])
    for v in idx[1:]:
        v = int(v)
        if v != p + 1:
            out.append((s, p))
            s = v
        p = v
    out.append((s, p))
    return out


def _pixelate(img: Image.Image, box, block=14):
    x0, y0, x1, y1 = [int(v) for v in box]
    x1, y1 = min(x1, img.width), min(y1, img.height)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    region = img.crop((x0, y0, x1, y1))
    small = region.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)), Image.BILINEAR)
    img.paste(small.resize((x1 - x0, y1 - y0), Image.NEAREST), (x0, y0))


def _fill(img: Image.Image, box, color):
    x0, y0, x1, y1 = [int(v) for v in box]
    x1, y1 = min(x1, img.width), min(y1, img.height)
    if x1 - x0 < 1 or y1 - y0 < 1:
        return
    img.paste(Image.new("RGB", (x1 - x0, y1 - y0), color), (x0, y0))


def find_kpi_band(a: np.ndarray):
    """Return (top, bottom) of the KPI card row, or None."""
    H, W, _ = a.shape
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    grey = (r >= CARD_GREY[0]) & (r <= CARD_GREY[1]) & (np.abs(r - g) < 5) & (np.abs(g - b) < 5)
    frac = grey.mean(axis=1)
    rows = np.where(frac > 0.3)[0]
    for s, e in _runs(rows):
        h = e - s
        if 36 <= h <= 170 and s < H * 0.55:
            return s, e
    return None


def find_bars(a: np.ndarray, y_from: int):
    """Return a list of (y0, y1, x_start, x_end) for horizontal bars (orange = Attribution, purple = Creator Connections)."""
    H, W, _ = a.shape
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    orange = (r > 230) & (g > 110) & (g < 190) & (b < 90)
    purple = (b > 215) & (r > 130) & (r < 205) & (g > 130) & (g < 205) & (b - r > 40)
    bar = orange | purple
    bar[:y_from] = False
    counts = bar.sum(axis=1)
    rows = np.where(counts >= BAR_MIN_PIXELS)[0]
    cands = []
    for s, e in _runs(rows):
        if e - s < 14:  # legend dots / avatars are shorter than a bar
            continue
        cols = np.where(bar[s:e + 1].any(axis=0))[0]
        cands.append((s, e, cols))
    if len(cands) < 4:
        return []
    starts = np.array([int(c[2].min()) for c in cands])
    mode = int(np.bincount(starts // 4).argmax() * 4)
    bars = []
    for s, e, cols in cands:
        cols = cols[cols >= mode - 8]  # ignore coloured avatars left of the bar column
        if len(cols) == 0 or abs(int(cols.min()) - mode) > 8:
            continue
        bars.append((s, e, int(cols.min()), int(cols.max())))
    return bars if len(bars) >= 4 else []


def redact(src, dst, *, block=14) -> dict:
    src, dst = Path(src), Path(dst)
    img = Image.open(src).convert("RGB")
    a = np.array(img)
    H, W, _ = a.shape
    log = {"source": src.name, "size": [W, H], "kpi_band": None, "bars": 0, "regions": []}

    band = find_kpi_band(a)
    if band:
        s, e = band
        h = e - s
        box = (int(W * 0.005), int(s + h * 0.42), int(W * 0.995), int(e - h * 0.06))
        _pixelate(img, box, block)
        log["kpi_band"] = [int(s), int(e)]
        log["regions"].append({"type": "kpi_values", "box": list(box), "method": "pixelate"})

    y_from = band[1] + 10 if band else int(H * 0.25)
    bars = find_bars(a, y_from)
    if bars:
        x_bar = min(b_[2] for b_ in bars)
        bg = tuple(int(v) for v in a[(bars[0][0] + bars[0][1]) // 2, max(0, x_bar - 3)])  # list background (gap before the bar)
        top, bottom = bars[0][0] - 10, bars[-1][1] + 12
        names_box = (max(0, x_bar - NAME_COL_WIDTH), top, x_bar - 8, bottom)
        _pixelate(img, names_box, block)
        log["regions"].append({"type": "creator_names", "box": list(names_box), "method": "pixelate"})
        for (y0, y1, _x0, x1) in bars:
            box = (x1 + 4, y0 - 8, min(W, x1 + AMOUNT_LABEL_WIDTH), y1 + 8)
            _fill(img, box, bg)
            log["regions"].append({"type": "amount_label", "box": list(box), "method": "fill"})
        log["bars"] = len(bars)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, optimize=True)
    return log


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(redact(sys.argv[1], sys.argv[2]))
