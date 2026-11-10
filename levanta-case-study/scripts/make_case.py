#!/usr/bin/env python3
"""One-shot pipeline: case folder → finished Levanta case deck (PPTX + PDF when LibreOffice is available) + QA report.

    python3 make_case.py --case <case_dir> [--skill <skill_root>] [--no-strategy] [--no-hook] [--name <file stem>]

Case folder layout (see references/input-checklist.md):
    case-config.json   category / periods / product / shots / conclusion / footers / notes / optional modules
    input.json         raw Sales, Conversions, Commission, BRB per brand (strings keep decimals)
    contact.json       name / role / email / qr_image  (the sender's own details — never reuse someone else's)
    sources/           the six backend screenshots (+ optional category media screenshots, QR image)
    strategy.json      optional (copy assets/strategy-page-default.json and fill in); omit or --no-strategy to skip
    overview.json      optional extra table page (same format as strategy.json, custom "columns"; e.g. 多品类案例速览)
    questions.json     optional (copy assets/hook-page-default.json); omit or --no-hook to skip

Outputs in <case_dir>/out/: <name>.pptx, <name>.pdf (if soffice), render/page-N.jpg (if pdftoppm), validation.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from calculate_metrics import calculate  # noqa: E402
from build import build  # noqa: E402
import add_strategy_page  # noqa: E402
import add_questions_page  # noqa: E402

FIXED_LABELS = {"指标", "品牌 A", "品牌 B", "品牌 C", "创作者报告", "品牌 A / B / C 后台截图", "主要产品",
                "归因销售额 Sales", "转化量 Conversions", "平均客单价 Sales / Conversions", "联盟佣金 Commission",
                "平均佣金率 Commission / Sales", "BRB 费用抵扣", "净佣金成本 Commission − BRB",
                "渠道 ROAS Sales / (Commission − BRB)", "净佣金成本率（类 ACOS）", "出单伙伴", "佣金与 BRB", "渠道效果"}


def die(msg):
    raise SystemExit(f"[make_case] {msg}")


def texts_of(slide):
    out = []
    for sh in slide.shapes:
        if sh.has_text_frame:
            out.append(sh.text_frame.text.strip())
        if sh.has_table:
            t = sh.table
            for r in range(len(t.rows)):
                for c in range(len(t.columns)):
                    out.append(t.cell(r, c).text.strip())
    return [x for x in out if x]


def validate_inputs(case: Path):
    for f in ("case-config.json", "input.json", "contact.json"):
        if not (case / f).exists():
            die(f"缺少 {f}")
    cfg = json.loads((case / "case-config.json").read_text(encoding="utf-8"))
    for key in ("category", "periods", "product", "shots", "conclusion", "slide2_footer", "notes"):
        if key not in cfg:
            die(f"case-config.json 缺少字段 {key}")
    src = case / "sources"
    for brand, pair in cfg["shots"].items():
        for f in pair:
            if not (src / f).exists():
                die(f"找不到截图 sources/{f}（{brand}）")
    mp = cfg.get("media_pages")
    if mp and not cfg.get("media_library"):
        imgs = []
        for page in ("slide4", "slide5"):
            for slot in mp.get(page, {}).get("slots", []):
                if not slot or slot.get("keep"):
                    continue
                imgs += [slot.get("image")] + [p["image"] for p in slot.get("pair", [])]
        imgs += [i["image"] for i in mp.get("slide5", {}).get("slot4", {}).get("images", [])]
        for f in filter(None, imgs):
            if not (src / f).exists():
                die(f"找不到媒体截图 sources/{f}")
    return cfg


def qa(pptx_path: Path, pdf_path: Path | None, case: Path, skill: Path, expected_pages: int):
    from pptx import Presentation
    report = {"file": pptx_path.name, "checks": {}}
    prs = Presentation(str(pptx_path))
    report["checks"]["page_count"] = {"expected": expected_pages, "actual": len(prs.slides), "ok": len(prs.slides) == expected_pages}
    pat = re.compile(r"^(\d\d) / (\d\d)$")
    nums = []
    for idx, s in enumerate(prs.slides, start=1):
        found = [pat.match(t) for t in texts_of(s)]
        found = [m for m in found if m]
        nums.append(found[0].group(0) if found else None)
    report["checks"]["page_numbers"] = {"values": nums, "ok": all(n == f"{i:02d} / {len(prs.slides):02d}" for i, n in enumerate(nums, start=1))}
    t1 = next(sh for sh in prs.slides[0].shapes if sh.has_table).table
    t3 = next(sh for sh in prs.slides[2].shapes if sh.has_table).table
    report["checks"]["tables"] = {"slide1_rows": len(t1.rows), "slide3_rows": len(t3.rows), "ok": len(t1.rows) == 11 and len(t3.rows) == 9}
    report["checks"]["slide1_values"] = {"brb": [t1.cell(7, c).text for c in range(1, 4)], "roas": [t1.cell(9, c).text for c in range(1, 4)],
                                        "acos": [t1.cell(10, c).text for c in range(1, 4)]}
    # leftovers from the template's sample case on slides 1–2
    tpl = Presentation(str(skill / "assets" / "reference.pptx"))
    tpl_texts = set(texts_of(tpl.slides[0]) + texts_of(tpl.slides[1])) - FIXED_LABELS
    out_texts = set(texts_of(prs.slides[0]) + texts_of(prs.slides[1]))
    leftovers = sorted(t for t in out_texts & tpl_texts if not pat.match(t))
    report["checks"]["template_leftovers_slides_1_2"] = {"items": leftovers, "ok": not leftovers}
    # backend ROAS cross-check when input.json carries backend_roas
    inp = json.loads((case / "input.json").read_text(encoding="utf-8"))
    cmp = []
    for b, cell in zip(inp["brands"], report["checks"]["slide1_values"]["roas"]):
        if b.get("backend_roas") is not None:
            shown = cell.replace("×", "")
            ok = shown == "—" or abs(float(shown) - float(b["backend_roas"])) <= 0.011
            cmp.append({"label": b["label"], "backend": b["backend_roas"], "shown": cell, "ok": ok})
    report["checks"]["roas_vs_backend"] = {"items": cmp, "ok": all(c["ok"] for c in cmp)}
    # QR consistency (optional, needs opencv)
    try:
        import io, hashlib, zipfile
        import cv2, numpy as np
        from PIL import Image
        contact = json.loads((case / "contact.json").read_text(encoding="utf-8"))
        qr_src = (case / contact["qr_image"]).read_bytes()
        det = cv2.QRCodeDetector()

        def decode(img):
            arr = np.array(img.convert("RGB"))[:, :, ::-1]
            h, w = arr.shape[:2]
            if w < 600:
                arr = cv2.resize(arr, (w * 3, h * 3), interpolation=cv2.INTER_NEAREST)
            return det.detectAndDecode(arr)[0]
        emb = None
        with zipfile.ZipFile(pptx_path) as z:
            for n in z.namelist():
                if n.startswith("ppt/media/") and hashlib.sha256(z.read(n)).hexdigest() == hashlib.sha256(qr_src).hexdigest():
                    emb = z.read(n)
        d0 = decode(Image.open(io.BytesIO(qr_src)))
        d1 = decode(Image.open(io.BytesIO(emb))) if emb else ""
        d2 = None
        if pdf_path and pdf_path.exists() and shutil.which("pdftoppm"):
            last = len(prs.slides)
            tmp = case / "out" / "_qr"
            subprocess.run(["pdftoppm", "-png", "-r", "200", "-f", str(last), "-l", str(last), str(pdf_path), str(tmp)], check=True)
            pg = Image.open(sorted((case / "out").glob("_qr*.png"))[0])
            W, H = pg.size
            d2 = decode(pg.crop((int(W * 887 / 1280), int(H * 215 / 720), int(W * 1187 / 1280), int(H * 499 / 720))))
            for f in (case / "out").glob("_qr*.png"):
                f.unlink()
        ok = bool(d0) and d0 == d1 and (d2 is None or d2 == d0)
        report["checks"]["qr"] = {"embedded_bytes_identical": emb is not None, "decode_consistent": ok, "pdf_checked": d2 is not None}
    except Exception as e:  # opencv missing etc.
        report["checks"]["qr"] = {"skipped": f"{type(e).__name__}: {e}"}
    report["ok"] = all(v.get("ok", True) for v in report["checks"].values() if isinstance(v, dict))
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True, type=Path)
    ap.add_argument("--skill", type=Path, default=HERE.parent)
    ap.add_argument("--no-strategy", action="store_true")
    ap.add_argument("--no-hook", action="store_true")
    ap.add_argument("--no-overview", action="store_true", help="skip overview.json even if present")
    ap.add_argument("--name", help="output file stem (default: Levanta_<类目>_案例与推广示例_<N页>_<YYYYMMDD>)")
    a = ap.parse_args()
    case, skill = a.case.resolve(), a.skill.resolve()
    cfg = validate_inputs(case)
    out = case / "out"
    out.mkdir(exist_ok=True)

    # 1) metrics
    inp = json.loads((case / "input.json").read_text(encoding="utf-8"))
    metrics = calculate(inp)
    (case / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    for b in metrics["brands"]:
        for w in b["warnings"]:
            print(f"[metrics] {b['label']}: {w}")

    # 2) six core pages
    cur = build(case, skill)

    # 3) optional strategy page (after slide 5)
    pages = 6
    if not a.no_strategy and (case / "strategy.json").exists():
        nxt = out / "candidate_s.pptx"
        add_strategy_page.main(str(cur), str(nxt), str(case / "strategy.json"))
        cur, pages = nxt, pages + 1
    # 3b) optional overview / extra table page (same renderer as the strategy page; its own insert_after)
    if not a.no_overview and (case / "overview.json").exists():
        nxt = out / "candidate_o.pptx"
        add_strategy_page.main(str(cur), str(nxt), str(case / "overview.json"))
        cur, pages = nxt, pages + 1
    # 4) optional hook page (before contact page)
    if not a.no_hook and (case / "questions.json").exists():
        nxt = out / "candidate_h.pptx"
        add_questions_page.main(str(cur), str(nxt), str(case / "questions.json"))
        cur, pages = nxt, pages + 1

    # 5) deliverable name + PDF
    cn = {6: "六页", 7: "七页", 8: "八页", 9: "九页"}[pages]
    stem = a.name or f"Levanta_{cfg['category'].replace(' ', '')}_案例与推广示例_{cn}_{dt.date.today():%Y%m%d}"
    final = out / f"{stem}.pptx"
    shutil.copyfile(cur, final)
    pdf = None
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), str(final)],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        pdf = out / f"{stem}.pdf"
        if not pdf.exists():
            pdf = None
            print("[make_case] PDF 导出失败，请在本机用 PowerPoint/Keynote 另存为 PDF")
        elif shutil.which("pdftoppm"):
            rd = out / "render"
            rd.mkdir(exist_ok=True)
            for f in rd.glob("page-*.jpg"):
                f.unlink()
            subprocess.run(["pdftoppm", "-jpeg", "-r", "80", str(pdf), str(rd / "page")], check=False)
    else:
        print("[make_case] 未找到 LibreOffice（soffice），只输出 PPTX；PDF 请在本机另存")

    # 6) QA
    report = qa(final, pdf, case, skill, pages)
    report["deliverables"] = [str(final)] + ([str(pdf)] if pdf else [])
    (out / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        print("[make_case] QA 有未通过项，见上方 validation.json；修正后重跑")
    for f in ("candidate.pptx", "candidate_s.pptx", "candidate_o.pptx", "candidate_h.pptx"):
        p = out / f
        if p.exists() and p != final:
            p.unlink()


if __name__ == "__main__":
    main()
