# 配置文件参考（case 目录）

一个案例目录长这样：

```
<case>/
├── case-config.json      页面文案与模块配置（必填）
├── input.json            三品牌原始数值（必填）
├── contact.json          发送人联系信息（必填）
├── strategy.json         策略页（可选；从 assets/strategy-page-default.json 复制后改）
├── structure.json        定向版“出单伙伴结构 × 覆盖现状”页（可选；范例 assets/structure-page-default.json，见 structure-page.md）
├── overview.json         额外表格页（可选；与 strategy.json 同一渲染器、自定义 columns；如“多品类案例速览”，范例 assets/overview-page.example.json）
├── questions.json        钩子页（可选；从 assets/hook-page-default.json 复制后改）
├── contact-qr.png        发送人二维码（contact.json 里引用）
├── sources/              六张后台截图 + 可选的媒体截图
└── out/                  脚本输出（PPTX / PDF / render / validation.json）
```

完整示例见 `assets/case-config.example.json`（儿童玩具与 DIY 案例，数字为真实案例，仅作格式参考，**不能当新案例的数据**）。

## input.json

```json
{
  "currency": "USD",
  "brands": [
    {"label": "品牌 A", "sales": "64609.01", "commission": "6722.03", "conversions": 894, "brb": "8151.50", "backend_roas": 0},
    {"label": "品牌 B", "sales": "70199.86", "commission": "11140.76", "conversions": 410, "brb": "4776.72", "backend_roas": 11.03},
    {"label": "品牌 C", "sales": "153680.97", "commission": "19936.77", "conversions": 857, "brb": "8498.78", "backend_roas": 13.44}
  ]
}
```

- 金额用字符串保留小数；`brb` 为报表值或用户补充值；VC 店铺写 `"0"` 并在 case-config 用 `brb_display_override` 把格子显示成“不适用（VC）”。
- `backend_roas`（可选）：后台卡片显示的 ROAS，QA 会和算出来的比对（允许 ±0.01；后台显示 0 表示 BRB 高于佣金）。

## contact.json

```json
{"name": "张三｜Levanta", "role": "行业解决方案专家｜Industry Solutions Consultant", "email": "zhangsan@levanta.io", "qr_image": "contact-qr.png"}
```

四项必填；`qr_image` 相对 case 目录。

## case-config.json 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `category` | ✓ | 类目标签，如 `"儿童玩具与 DIY 类"`；进标题、眉题、文件名 |
| `year` | | 默认 `"2026"` |
| `period_word` | | 默认 `"近三个月"`；两个月写 `"近两个月"` |
| `periods` | ✓ | `{"品牌 A": "0801–1031", …}`；三者一致时第 1/2 页写统一统计期，否则分别标注 |
| `period_line_override` | | 覆盖第 1 页统计期整行，如多站点：`"近三个月（0801–1031）· 2026年｜A/C：美国站；B：美国站＋独立站＋英德站｜金额：美元"` |
| `period_words` | | 按品牌覆盖“近三个月”这个词，如 `{"品牌 C": "近两个月"}`（某品牌统计期长度不同时用，第 2 页该品牌的期标签随之改） |
| `slide2_subtitle_override` | | 覆盖第 2 页副标题整行（统计期不一致且默认句式不合适时） |
| `product` | ✓ | `{"品牌 A": ["中文", "English"], …}`；第 1 页两行，第 2 页写“中文（English）” |
| `shots` | ✓ | `{"品牌 A": ["效果报告.png", "创作者报告.png"], …}`，文件在 `sources/` |
| `brb_display_override` | | `{"品牌 A": "不适用（VC）"}`，只改显示 |
| `redact_shots` | | 默认 `true`：第 2 页截图嵌入前打码（KPI 数值、创作者名称/头像、金额）。设 `false` 才用原图，仅限负责人要求且不外发 |
| `slide1_eyebrow` / `slide1_title` | | 定向版眉题“为 ×× 准备 · ××类品牌案例”；标题一般不改 |
| `conclusion.title` | ✓ | “案例结论：……”一行 |
| `conclusion.partners` | ✓ | 1–2 行；只点名有成交且身份明确的主体 |
| `conclusion.brb` | ✓ | 1 行（2 行时 partners 须为 1 行） |
| `conclusion.effect` | ✓ | 1 行 |
| `conclusion.source_footer_uniform` / `source_footer_split` | ✓ | 统计期一致/不一致时用的页脚 |
| `conclusion.footnotes` | ✓ | 两条注脚：类 ACOS 定义 + BRB 口径说明 |
| `slide2_footer` | ✓ | 第 2 页页脚：站点口径、BRB 是报表值/补充值/不适用 |
| `notes.slide1` / `notes.slide2` | ✓ | 演讲者备注：原始值、计算、伙伴依据与金额、产品来源、政策入口 |
| `cost_tiers` | | **一般不填**。`{"tiers": [..], "tier_labels": [..], "commission_rate": "0.15", "platform_rate": "0.035", "brb_rate": "0.10", "monthly_fee": "600"}` |
| `cost_page_text` | | `{"eyebrow", "footer", "notes_prefix"}`，配合 `cost_tiers` 用 |
| `media_library` | | 引用品类示例包，如 `"家居安防类"`；脚本自动加载 `assets/media-library/<品类>/media_pages.json` 并把图复制进 `sources/` |
| `media_pages` | | 第 4–5 页自定义换图，结构见 `media-pages.md`；与 `media_library` 同时存在时以 `media_pages` 为准 |

每行文字长度：结论每行约 70 个中文字等宽以内；第 2 页产品标签超过 30 字符会自动缩到 9.5pt。

## strategy.json / questions.json

分别见 `strategy-page.md`、`hook-page.md`。两者都带 `insert_after`（策略页默认 5）与版式参数；从 assets 复制后只改文字。

## 运行

```bash
python3 scripts/make_case.py --case <case>              # 默认：有 strategy.json 就加策略页，有 questions.json 就加钩子页
python3 scripts/make_case.py --case <case> --no-strategy --no-hook   # 六页
python3 scripts/make_case.py --case <case> --no-overview             # 有 overview.json 但本次不要
python3 scripts/make_case.py --case <case> --name Levanta_家居安防类_BILLCONCH定向_案例与推广示例_八页_20261106
```

输出 `out/<name>.pptx`（+ `.pdf`、`render/page-N.jpg`、`validation.json`）。`validation.json` 的 `ok` 为 false 时看 `checks` 里哪项失败。
