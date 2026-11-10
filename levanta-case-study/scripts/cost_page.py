#!/usr/bin/env python3
"""Rewrite the fixed cost-and-performance page (slide 3) of a Levanta case deck from a tier config.

Model (cost-and-performance.md): C = S × (c + p − b) + F
  c = creator commission rate, p = platform fee rate, b = BRB rate, F = monthly platform fee.
Default tiers: $10,000 / $30,000 / $100,000 (起步 / 成长 / 规模), confirmed 2026-11-03.

Usage as a module:  apply_cost_tiers(prs, cfg)        # prs = python-pptx Presentation
Usage as a script:  python3 cost_page.py <in.pptx> <out.pptx> [tiers.json]
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal, ROUND_HALF_UP

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

DEFAULT = {
    "tiers": [10000, 30000, 100000],
    "tier_labels": ["起步情景", "成长情景", "规模情景"],
    "commission_rate": "0.15",
    "platform_rate": "0.035",
    "brb_rate": "0.10",
    "monthly_fee": "600",
}


def _q(tag):
    return "{%s}%s" % (A_NS, tag)


def set_lines(text_frame, lines):
    txBody = text_frame._txBody
    paras = txBody.findall(_q("p"))
    proto = copy.deepcopy(paras[0])
    runs = proto.findall(_q("r"))
    for extra in runs[1:]:
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


def money(v: Decimal) -> str:
    v = v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ("−$" if v < 0 else "$") + format(abs(v), ",.0f")


def pct(v: Decimal) -> str:
    return str((v * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) + "%"


def pct1(v: Decimal) -> str:
    s = (v * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return (str(s).rstrip("0").rstrip(".") if "." in str(s) else str(s)) + "%"


def mult(v: Decimal) -> str:
    return str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) + "×"


def compute(cfg):
    c, p, b, F = (Decimal(cfg["commission_rate"]), Decimal(cfg["platform_rate"]),
                  Decimal(cfg["brb_rate"]), Decimal(cfg["monthly_fee"]))
    rows = []
    for S in cfg["tiers"]:
        S = Decimal(S)
        comm, plat, brb = S * c, S * p, S * b
        net = comm + plat + F - brb
        rows.append(dict(S=S, comm=comm, plat=plat, fee=F, brb=brb, net=net, rate=net / S, roi=S / net))
    return rows, (c + p - b)


def apply_cost_tiers(prs, cfg=None):
    cfg = {**DEFAULT, **(cfg or {})}
    rows, var_rate = compute(cfg)
    s = prs.slides[2]
    tbl = next(sh for sh in s.shapes if sh.has_table).table
    assert len(tbl.rows) == 9 and len(tbl.columns) == 4, "slide 3 table must be 9x4"
    assert tbl.cell(1, 0).text.startswith("月归因销售额"), tbl.cell(1, 0).text
    for c_idx, label in enumerate(cfg["tier_labels"], start=1):
        set_lines(tbl.cell(0, c_idx).text_frame, [label])
    for c_idx, r in enumerate(rows, start=1):
        vals = [money(r["S"]), money(r["comm"]), money(r["plat"]), money(r["fee"]), money(-r["brb"]),
                money(r["net"]), pct(r["rate"]), mult(r["roi"])]
        for r_idx, v in enumerate(vals, start=1):
            set_lines(tbl.cell(r_idx, c_idx).text_frame, [v])

    def by_name(name):
        return next(sh for sh in s.shapes if sh.name == name)

    lo, hi = rows[0], rows[-1]
    roi_lo, roi_hi = min(r["roi"] for r in rows), max(r["roi"] for r in rows)
    rate_lo, rate_hi = min(r["rate"] for r in rows), max(r["rate"] for r in rows)
    set_lines(by_name("案例结论正文 出单伙伴").text_frame, [
        f"在上述测算下，每投入 $1 净推广成本，对应约 ${roi_lo.quantize(Decimal('0.01'))}–${roi_hi.quantize(Decimal('0.01'))} 归因销售额。",
        f"净推广成本率约为 {pct1(rate_lo)}–{pct1(rate_hi)}，可与现有渠道的同口径成本作对照。",
    ])
    set_lines(by_name("案例结论正文 佣金与 BRB").text_frame, [
        f"扣除 BRB 后，净推广成本＝归因销售额 × {pct1(var_rate)}＋${int(Decimal(cfg['monthly_fee']))}/月。"])
    set_lines(by_name("案例结论正文 渠道效果").text_frame, [
        f"销售规模扩大，固定月费占比逐步降低；月归因销售达 {money(hi['S'])} 时，净推广成本率为 {pct1(hi['rate'])}，逐步趋近 {pct1(var_rate)}。"])
    tiers_txt = "、".join(money(r["S"]) for r in rows)
    s.notes_slide.notes_text_frame.text = (
        "原始模型来源：LIFENGSOLER_美国太阳能灯_站外推广方案_对客版_v3_20261021.pptx 第12页；标题与结论按用户2026-10-28确认；"
        f"三档销售情景按用户2026-11-03确认改为 {tiers_txt}（原 $10,000/$20,000/$40,000 只覆盖起步段，改为等比三档以覆盖中小到规模卖家）。"
        f"月度假设：创作者佣金{pct1(Decimal(cfg['commission_rate']))}、平台费{pct1(Decimal(cfg['platform_rate']))}、单品牌优惠月费${int(Decimal(cfg['monthly_fee']))}、BRB {pct1(Decimal(cfg['brb_rate']))}。"
        f"净推广成本=S×{pct1(var_rate)}+{int(Decimal(cfg['monthly_fee']))}。"
        + "；".join(f"S={money(r['S'])}：净成本{money(r['net'])}、成本率{pct(r['rate'])}、投入产出比{mult(r['roi'])}" for r in rows)
        + "。此为情景测算，不是案例品牌实际费用或销售预测；已计平台费、月费，与第1页净佣金口径不同；样品、物流、固定内容合作费另计。BRB按合格美国站Amazon Attribution销售测算，案例中BRB占销售额比例因类目差异较大（约1%–14%），实际以Amazon核算为准。BRB政策来源：https://sell.amazon.com/blog/brand-referral-bonus。"
    )
    return rows


def main():
    from pptx import Presentation
    src, dst = sys.argv[1], sys.argv[2]
    cfg = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 else None
    prs = Presentation(src)
    rows = apply_cost_tiers(prs, cfg)
    prs.save(dst)
    for r in rows:
        print(money(r["S"]), money(r["net"]), pct(r["rate"]), mult(r["roi"]))
    print("saved", dst)


if __name__ == "__main__":
    main()
