#!/usr/bin/env python3
"""Build the six core pages of a Levanta case deck from the reference template.

    python3 build.py --case <case_dir> [--skill <skill_root>]

Reads from <case_dir>:  case-config.json, metrics.json (from calculate_metrics.py), contact.json,
                        sources/<screenshots>
Writes to  <case_dir>/out/candidate.pptx and <case_dir>/out/picture-fit.json

Pages 1–2 are rebuilt from this case's verified data; page 3 keeps the template cost model unless
`cost_tiers` is configured; pages 4–5 keep the template's cross-category examples unless `media_pages`
is configured; page 6 is personalised from contact.json. Strategy and hook pages are added afterwards by
add_strategy_page.py / add_questions_page.py (make_case.py runs the whole chain).
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cost_page import apply_cost_tiers  # noqa: E402
from media_pages import apply_media_pages  # noqa: E402
from contact_page import apply_contact  # noqa: E402
from redact_shots import redact  # noqa: E402

EMU_PER_PX = 12192000 / 1280  # 9525
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
BRANDS = ["品牌 A", "品牌 B", "品牌 C"]


def _q(tag: str) -> str:
    return "{%s}%s" % (A_NS, tag)


def set_lines(text_frame, lines):
    """Replace all paragraphs with one paragraph per line, cloning the first paragraph's formatting."""
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
        t = p.find(_q("r")).find(_q("t"))
        t.text = line
        if line != line.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
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


def px(v):
    return Emu(int(round(v * EMU_PER_PX)))


def replace_picture(slide, pic, png_path: Path, slot_x, slot_y, slot_w, slot_h, crop=(0, 0, 0, 0)):
    """Embed the original bytes, contain-fit into the slot (centred, top-aligned); crop is visible-only."""
    data = png_path.read_bytes()
    im = Image.open(io.BytesIO(data))
    full_w, full_h = im.size
    iw = full_w * (1 - crop[0] - crop[2])
    ih = full_h * (1 - crop[1] - crop[3])
    part = slide.part.related_part(pic._element.blip_rId)
    part._blob = data
    scale = min(slot_w / iw, slot_h / ih)
    w, h = iw * scale, ih * scale
    x = slot_x + (slot_w - w) / 2
    pic.left, pic.top, pic.width, pic.height = px(x), px(slot_y), px(w), px(h)
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = crop
    return {"image": [full_w, full_h], "crop": list(crop), "frame_px": [round(x, 1), round(slot_y, 1), round(w, 1), round(h, 1)]}


def resolve_media_pages(cfg: dict, skill_root: Path, sources: Path):
    """`media_pages` in case-config wins; otherwise `media_library: "<品类>"` loads assets/media-library/<品类>/media_pages.json
    and copies that pack's images into the case's sources/ (only files that are not already there)."""
    if cfg.get("media_pages"):
        return cfg["media_pages"]
    lib = cfg.get("media_library")
    if not lib:
        return None
    pack = skill_root / "assets" / "media-library" / lib
    if not (pack / "media_pages.json").exists():
        raise SystemExit(f"media_library 「{lib}」不存在：assets/media-library/ 下可用：{sorted(p.name for p in (skill_root / 'assets' / 'media-library').iterdir() if p.is_dir())}")
    mp = json.loads((pack / "media_pages.json").read_text(encoding="utf-8"))
    sources.mkdir(exist_ok=True)
    for img in pack.glob("*.png"):
        if not (sources / img.name).exists():
            shutil.copyfile(img, sources / img.name)
    return mp


def build(case_dir: Path, skill_root: Path):
    cfg = json.loads((case_dir / "case-config.json").read_text(encoding="utf-8"))
    metrics = json.loads((case_dir / "metrics.json").read_text(encoding="utf-8"))
    contact = json.loads((case_dir / "contact.json").read_text(encoding="utf-8"))
    sources = case_dir / "sources"
    out_dir = case_dir / "out"
    out_dir.mkdir(exist_ok=True)
    template = skill_root / "assets" / "reference.pptx"

    disp = {b["label"]: dict(b["display"]) for b in metrics["brands"]}
    category = cfg["category"]
    periods = cfg["periods"]
    product = cfg["product"]
    shots = cfg["shots"]
    uniform = len(set(periods.values())) == 1
    period_word = cfg.get("period_word", "近三个月")
    year = cfg.get("year", "2026")

    prs = Presentation(str(template))
    assert len(prs.slides) == 6, "reference.pptx must be the 6-page template"
    log = {}

    # ---- display tweaks: negative net cost → "−$x" and "—" for ROAS/类ACOS; explicit BRB cell overrides (e.g. VC 店铺)
    for b in BRANDS:
        d = disp[b]
        if d["net_commission_cost"].startswith("$-"):
            d["net_commission_cost"] = "−$" + d["net_commission_cost"][2:]
            d["channel_roas"] = "—"
            d["net_commission_cost_rate"] = "—"
    for b, txt in cfg.get("brb_display_override", {}).items():
        disp[b]["brb"] = txt
    period_line = cfg.get("period_line_override") or (
        f"{period_word}（{periods['品牌 A']}）· {year}年｜美国站｜金额：美元" if uniform else
        f"{period_word} · {year}年｜A/B：{periods['品牌 A']}，C：{periods['品牌 C']}｜美国站｜金额：美元")

    # ---------------------------------------------------------------- slide 1
    s1 = prs.slides[0]
    set_lines(by_name(s1, "Text 0").text_frame, [cfg.get("slide1_eyebrow") or f"{category} · 品牌案例"])
    title = by_name(s1, "Text 1")
    set_lines(title.text_frame, [cfg.get("slide1_title") or f"{category}品牌在 Levanta 的联盟营销效果"])
    table_frame = next(sh for sh in s1.shapes if sh.has_table)
    title.width = table_frame.width
    set_lines(by_name(s1, "Text 2").text_frame, [period_line])

    tbl = table_frame.table
    assert len(tbl.rows) == 11 and len(tbl.columns) == 4
    assert [tbl.cell(0, c).text for c in range(4)] == ["指标", "品牌 A", "品牌 B", "品牌 C"]
    keys = [None, "sales", "conversions", "average_order_value", "commission", "commission_rate",
            "brb", "net_commission_cost", "channel_roas", "net_commission_cost_rate"]
    for r, key in enumerate(keys, start=1):
        for c, brand in enumerate(BRANDS, start=1):
            set_lines(tbl.cell(r, c).text_frame, product[brand] if key is None else [disp[brand][key]])

    con = cfg["conclusion"]
    set_lines(by_name(s1, "案例结论标题").text_frame, [con["title"]])
    set_lines(by_name(s1, "案例结论正文 出单伙伴").text_frame, con["partners"])
    set_lines(by_name(s1, "案例结论正文 佣金与 BRB").text_frame, con["brb"])
    set_lines(by_name(s1, "案例结论正文 渠道效果").text_frame, con["effect"])
    if len(con["partners"]) == 1 and len(con["brb"]) == 2:  # re-flow when 佣金与BRB needs two lines
        for nm, y, h in (("出单伙伴", 532, 25), ("佣金与 BRB", 563, 43), ("渠道效果", 611, 25)):
            for prefix in ("案例结论标签 ", "案例结论正文 "):
                sh = by_name(s1, prefix + nm)
                sh.top, sh.height = px(y), px(h)
    set_lines(by_name(s1, "Source footer").text_frame, [con["source_footer_uniform" if uniform else "source_footer_split"]])
    set_lines(by_name(s1, "P5 text 101").text_frame, con["footnotes"])
    s1.notes_slide.notes_text_frame.text = cfg["notes"].get("slide1", "")

    # ---------------------------------------------------------------- slide 2
    s2 = prs.slides[1]
    set_lines(by_id(s2, 24).text_frame, [f"{category} · 后台报告"])
    assert by_id(s2, 2).text_frame.text == "品牌 A / B / C 后台截图"
    sub = cfg.get("slide2_subtitle_override") or (
        f"{year}年{period_word}（{periods['品牌 A']}）｜上：效果报告　下：创作者报告｜可放大查看" if uniform else
        f"{year}年{period_word}｜A/B：{periods['品牌 A']}，C：{periods['品牌 C']}｜上：效果报告　下：创作者报告｜可放大查看")
    set_lines(by_id(s2, 3).text_frame, [sub])
    period_words = cfg.get("period_words", {})  # per-brand override of the "近三个月" word (e.g. one brand covers two months)
    redact_on = bool(cfg.get("redact_shots", True))  # default ON: backend screenshots are masked unless the config says otherwise
    ids = {"品牌 A": (5, 6, 7, 9), "品牌 B": (11, 12, 13, 15), "品牌 C": (17, 18, 19, 21)}
    cols = {"品牌 A": 52.8, "品牌 B": 452.16, "品牌 C": 851.52}
    for brand, (pid, perid, eff_id, cr_id) in ids.items():
        pl = product[brand]
        label = f"{pl[0]}（{pl[1]}）" if len(pl) == 2 else "／".join(pl)
        set_lines(by_id(s2, pid).text_frame, [label])
        if len(label) > 30:  # long label: unify to 9.5pt so it stays on one line (template: A/C 10.5pt, B 9.15pt)
            for p_ in by_id(s2, pid).text_frame.paragraphs:
                for r_ in p_.runs:
                    r_.font.size = Emu(int(9.5 * 12700))
        set_lines(by_id(s2, perid).text_frame, [f"{period_words.get(brand, period_word)}（{periods[brand]}）｜效果报告"])
        eff, cr = shots[brand]
        eff_path, cr_path = sources / eff, sources / cr
        if redact_on:  # data-compliance: pixelate KPI values, creator names and per-creator amounts before embedding
            red_dir = out_dir / "redacted"
            eff_path, cr_path = red_dir / f"{Path(eff).stem}_打码.png", red_dir / f"{Path(cr).stem}_打码.png"
            log.setdefault("redaction", {})[brand] = {"效果报告": redact(sources / eff, eff_path), "创作者报告": redact(sources / cr, cr_path)}
        log[brand] = {
            "效果报告": replace_picture(s2, by_id(s2, eff_id), eff_path, cols[brand], 236, 382.08, 188),
            "创作者报告": replace_picture(s2, by_id(s2, cr_id), cr_path, cols[brand], 450, 382.08, 234),
        }
    set_lines(by_id(s2, 22).text_frame, [cfg["slide2_footer"]])
    s2.notes_slide.notes_text_frame.text = cfg["notes"].get("slide2", "")

    # ---------------------------------------------------------------- slide 3: cost model (template default unless configured)
    if cfg.get("cost_tiers"):
        apply_cost_tiers(prs, cfg["cost_tiers"])
    s3 = prs.slides[2]
    cp = cfg.get("cost_page_text", {})
    if cp.get("eyebrow"):
        set_lines(by_name(s3, "Text 0").text_frame, [cp["eyebrow"]])
    if cp.get("footer"):
        set_lines(by_name(s3, "Source footer").text_frame, [cp["footer"]])
    if cp.get("notes_prefix"):
        s3.notes_slide.notes_text_frame.text = cp["notes_prefix"] + "\n" + s3.notes_slide.notes_text_frame.text

    # ---------------------------------------------------------------- slides 4–5: category media swap (optional)
    mp = resolve_media_pages(cfg, skill_root, sources)
    if mp:
        apply_media_pages(prs, mp, sources, log)

    # ---------------------------------------------------------------- slide 6: contact page (always personalised)
    apply_contact(prs, contact, case_dir, log)

    for i in range(2, 6):
        pn = next(sh for sh in prs.slides[i].shapes if sh.has_text_frame and sh.text_frame.text.strip().endswith("/ 06"))
        assert pn.text_frame.text.strip() == f"0{i+1} / 06"

    out = out_dir / "candidate.pptx"
    prs.save(str(out))
    (out_dir / "picture-fit.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True, type=Path)
    ap.add_argument("--skill", type=Path, default=HERE.parent)
    a = ap.parse_args()
    build(a.case.resolve(), a.skill.resolve())


if __name__ == "__main__":
    main()
