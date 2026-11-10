#!/usr/bin/env python3
"""Config-driven swap of the two '联盟伙伴推广形式示例' pages (template slides 4–5) for one case.

Call from build.py after slides 1–3 are written and before the hook/strategy pages are added:

    from media_pages import apply_media_pages
    apply_media_pages(prs, cfg["media_pages"], SOURCES, log)

Config (case-config.json → "media_pages"):
{
  "slide4": {"eyebrow"?, "title"?, "subtitle"?, "footer"?, "notes"?,
             "slots": [ {image, name, caption (str | [2 lines]), purpose, crop?: [l,t,r,b]}  × 3
                        — a slot given as null or {"keep": true} keeps the template's cross-category example
                        — or for one slot: {name, caption, purpose, "image": <first>,
                                            "pair": [{image, crop?, height?}, {image, crop?}]} ]},
  "slide5": {"eyebrow"?, "title"?, "subtitle"?, "footer"?, "notes"?, "summary"?: [2 lines],
             "slots": [ {image, name, caption, purpose, crop?} × 3 ],
             "slot4"?: {name, caption, purpose, "images": [{image, crop?}, {image, crop?}]}}   # Media Buyer column
}
Slide-4 slots are 374.4×365 px at x = 52.8 / 452.8 / 852.8 (y 189); slide-5 slots 279.2×292 at
x = 52.8 / 351.2 / 649.6 (y 191); slot4 holds two stacked pictures (279.2×144.5 at y191, 279.2×135 at y348).
Pictures are contain-fitted, horizontally centred, top-aligned; original bytes are embedded; crop is visible-only.
"""
from __future__ import annotations

import copy
import io
from pathlib import Path

from PIL import Image
from pptx.util import Emu

EMU_PER_PX = 12192000 / 1280
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _q(tag):
    return "{%s}%s" % (A_NS, tag)


def px(v):
    return Emu(int(round(v * EMU_PER_PX)))


def set_lines(text_frame, lines):
    txBody = text_frame._txBody
    paras = txBody.findall(_q("p"))
    proto = copy.deepcopy(paras[0])
    for extra in proto.findall(_q("r"))[1:]:
        proto.remove(extra)
    for tag in ("br", "fld"):
        for el in proto.findall(_q(tag)):
            proto.remove(el)
    for p in paras:
        txBody.remove(p)
    for line in lines:
        p = copy.deepcopy(proto)
        p.find(_q("r")).find(_q("t")).text = line
        txBody.append(p)


def by_name(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def by_id(slide, sid):
    for sh in slide.shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(sid)


def _visible_size(path, crop):
    im = Image.open(path)
    return im.size, im.size[0] * (1 - crop[0] - crop[2]), im.size[1] * (1 - crop[1] - crop[3])


def replace_picture(slide, pic, png_path: Path, slot_x, slot_y, slot_w, slot_h, crop=(0, 0, 0, 0)):
    data = png_path.read_bytes()
    full, iw, ih = _visible_size(io.BytesIO(data), crop)
    part = slide.part.related_part(pic._element.blip_rId)
    part._blob = data
    scale = min(slot_w / iw, slot_h / ih)
    w, h = iw * scale, ih * scale
    x = slot_x + (slot_w - w) / 2
    pic.left, pic.top, pic.width, pic.height = px(x), px(slot_y), px(w), px(h)
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = crop
    return {"image": list(full), "crop": list(crop), "frame_px": [round(x, 1), round(slot_y, 1), round(w, 1), round(h, 1)]}


def _lines(v):
    return v if isinstance(v, list) else [v]


def _header(slide, spec):
    for key, nm in (("title", "Slide title"), ("subtitle", "Subtitle"), ("footer", "Source footer"), ("eyebrow", "Section eyebrow")):
        if spec.get(key):
            set_lines(by_name(slide, nm).text_frame, [spec[key]])
    if "notes" in spec:
        slide.notes_slide.notes_text_frame.text = spec["notes"]


def apply_media_pages(prs, mp, sources: Path, log: dict):
    sources = Path(sources)
    # ---------------------------------------------------------------- slide 4
    s4 = prs.slides[3]
    slots4 = [(52.8, 374.4, 9, "Outdoor Life name", "Editorial caption", "Editorial purpose"),
              (452.8, 374.4, 10, "BuyeReviews name", "Roundup caption", "Roundup purpose"),
              (852.8, 374.4, 11, "KOL name", "KOL caption", "KOL purpose")]
    for (x, w, pid, nm, cap, pur), item in zip(slots4, mp["slide4"]["slots"]):
        if not item or item.get("keep"):  # null / {"keep": true} leaves the template's cross-category example in place
            continue
        set_lines(by_name(s4, nm).text_frame, [item["name"]])
        set_lines(by_name(s4, cap).text_frame, _lines(item["caption"]))
        set_lines(by_name(s4, pur).text_frame, [item["purpose"]])
        pic = by_id(s4, pid)
        assert pic.shape_type == 13
        if item.get("pair"):
            a, b = item["pair"]
            ca, cb = tuple(a.get("crop", (0, 0, 0, 0))), tuple(b.get("crop", (0, 0, 0, 0)))
            _, iaw, iah = _visible_size(sources / a["image"], ca)
            ha = a.get("height", 365)
            gap = 10
            wa = min(ha * iaw / iah, w * 0.62)
            log[f"第4页_{item['name']}_a"] = replace_picture(s4, pic, sources / a["image"], x, 189, wa, ha, crop=ca)
            pic.left = px(x)  # pin the first picture to the slot's left edge
            full_b, ibw, ibh = _visible_size(sources / b["image"], cb)
            wb_slot = w - wa - gap
            scale = min(wb_slot / ibw, 365 / ibh)
            wb, hb = ibw * scale, ibh * scale
            pic2 = s4.shapes.add_picture(str(sources / b["image"]), px(x + wa + gap), px(189), px(wb), px(hb))
            pic2.crop_left, pic2.crop_top, pic2.crop_right, pic2.crop_bottom = cb
            pic2.name = f"{item['name']} picture 2"
            log[f"第4页_{item['name']}_b"] = {"image": list(full_b), "crop": list(cb), "frame_px": [round(x + wa + gap, 1), 189, round(wb, 1), round(hb, 1)]}
        else:
            log[f"第4页_{item['name']}"] = replace_picture(s4, pic, sources / item["image"], x, 189, w, 365, crop=tuple(item.get("crop", (0, 0, 0, 0))))
    _header(s4, mp["slide4"])

    # ---------------------------------------------------------------- slide 5
    s5 = prs.slides[4]
    slots5 = [(52.8, 279.2, 10, "Publisher 0", "Type 0 caption", "Type 0 purpose"),
              (351.2, 279.2, 11, "Publisher 1", "Type 1 caption", "Type 1 purpose"),
              (649.6, 279.2, 12, "Publisher 2", "Type 2 caption", "Type 2 purpose")]
    for (x, w, pid, nm, cap, pur), item in zip(slots5, mp["slide5"]["slots"]):
        if not item or item.get("keep"):
            continue
        set_lines(by_name(s5, nm).text_frame, [item["name"]])
        set_lines(by_name(s5, cap).text_frame, _lines(item["caption"]))
        set_lines(by_name(s5, pur).text_frame, [item["purpose"]])
        pic = by_id(s5, pid)
        assert pic.shape_type == 13
        log[f"第5页_{item['name']}"] = replace_picture(s5, pic, sources / item["image"], x, 191, w, 292, crop=tuple(item.get("crop", (0, 0, 0, 0))))
    if mp["slide5"].get("summary"):
        set_lines(by_name(s5, "Levanta summary").text_frame, mp["slide5"]["summary"])
    if mp["slide5"].get("type3_caption"):
        set_lines(by_name(s5, "Type 3 caption").text_frame, _lines(mp["slide5"]["type3_caption"]))
    s4slot = mp["slide5"].get("slot4")
    if s4slot:
        set_lines(by_name(s5, "Publisher 3").text_frame, [s4slot["name"]])
        set_lines(by_name(s5, "Type 3 caption").text_frame, _lines(s4slot["caption"]))
        set_lines(by_name(s5, "Type 3 purpose").text_frame, [s4slot["purpose"]])
        for pid, (y, h), item in zip((13, 14), ((191, 144.5), (348, 135)), s4slot["images"]):
            pic = by_id(s5, pid)
            assert pic.shape_type == 13
            log[f"第5页_MediaBuyer_{pid}"] = replace_picture(s5, pic, sources / item["image"], 948.0, y, 279.2, h, crop=tuple(item.get("crop", (0, 0, 0, 0))))
    _header(s5, mp["slide5"])
    return log
