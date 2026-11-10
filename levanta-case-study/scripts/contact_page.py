#!/usr/bin/env python3
"""Personalise the fixed contact page (template slide 6) from contact.json.

contact.json:
{
  "name": "张三｜Levanta",                                   # 姓名行（建议“姓名｜Levanta”）
  "role": "行业解决方案专家｜Industry Solutions Consultant",  # 中英文职称，一行
  "email": "zhangsan@levanta.io",
  "qr_image": "contact-qr.png"                              # 相对 case 目录；企业微信/微信二维码原图，不重绘不裁边
}
Only these four items change; the headline, scenario line, invitation copy and the Levanta logo stay as in the
template. The role box is widened to 420px / 11.5pt so long bilingual titles stay on one line in LibreOffice renders.
"""
from __future__ import annotations

import copy
import io
from pathlib import Path

from PIL import Image
from pptx.util import Emu

EMU_PER_PX = 12192000 / 1280
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
REQUIRED = ("name", "role", "email", "qr_image")


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


def validate(cfg: dict, case_dir: Path):
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        raise SystemExit(f"contact.json 缺少必填项：{', '.join(missing)}（联系页必须是本次发送人自己的姓名、职称、邮箱和二维码）")
    qr = case_dir / cfg["qr_image"]
    if not qr.exists():
        raise SystemExit(f"找不到二维码图片：{qr}")
    return qr


def apply_contact(prs, cfg: dict, case_dir: Path, log: dict | None = None):
    qr_path = validate(cfg, Path(case_dir))
    s = prs.slides[5]
    set_lines(by_name(s, "Contact name").text_frame, [cfg["name"]])
    set_lines(by_name(s, "Contact email").text_frame, [cfg["email"]])
    role = by_name(s, "Contact role")
    set_lines(role.text_frame, [cfg["role"]])
    centre = role.left + role.width / 2
    role.width = px(420)
    role.left = Emu(int(round(centre - role.width / 2)))
    for p in role.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Emu(int(11.5 * 12700))

    # QR: the picture whose frame sits in the right column at y≈215 (template id 6); contain-fit into 300×284, centred
    pics = [sh for sh in s.shapes if sh.shape_type == 13]
    qr_pic = min(pics, key=lambda sh: abs(sh.top / EMU_PER_PX - 215) + abs(sh.left / EMU_PER_PX - 887))
    data = qr_path.read_bytes()
    im = Image.open(io.BytesIO(data))
    part = s.part.related_part(qr_pic._element.blip_rId)
    part._blob = data
    slot_x, slot_y, slot_w, slot_h = 887.0, 215.0, 300.0, 284.0
    scale = min(slot_w / im.size[0], slot_h / im.size[1])
    w, h = im.size[0] * scale, im.size[1] * scale
    x, y = slot_x + (slot_w - w) / 2, slot_y + (slot_h - h) / 2
    qr_pic.left, qr_pic.top, qr_pic.width, qr_pic.height = px(x), px(y), px(w), px(h)
    qr_pic.crop_left = qr_pic.crop_top = qr_pic.crop_right = qr_pic.crop_bottom = 0
    if log is not None:
        log["联系页二维码"] = {"image": list(im.size), "frame_px": [round(x, 1), round(y, 1), round(w, 1), round(h, 1)], "source": str(qr_path.name)}
    s.notes_slide.notes_text_frame.text = (
        f"联系页按 contact.json 个性化：{cfg['name']} / {cfg['role']} / {cfg['email']}；二维码来自 {qr_path.name}（原字节嵌入、等比缩放、未裁切、未重绘）。"
        "其余文案与 Logo 为模板固定内容。导出后需比对二维码原图/内嵌/PDF 渲染的解码结果一致（只比较，不打开链接）。")
    return qr_path
