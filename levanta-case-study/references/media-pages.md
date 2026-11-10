# 可配置模块：第 4–5 页推广形式示例换图（`scripts/media_pages.py`）

模板第 4–5 页默认是跨类目示例。用户为某个类目提供了公开媒体截图时，用本模块把两页整体换成该品类版本：图、站名、栏标题、说明、眉题、标题、副标题、页脚、备注全部由 `case-config.json` 的 `media_pages` 字段驱动，不手改 PPT。

## 调用

```python
# build.py 已自动调用：case-config.json 里有 media_pages 字段即生效
apply_media_pages(prs, cfg["media_pages"], case_dir / "sources", log)
```

## 槽位

| 页 | 槽 | 图片 id | 槽位（x, y, w, h，逻辑像素） | 名称 / 栏标题 / 说明对象名 |
|---|---|---|---|---|
| 4 | 1–3 | 9 / 10 / 11 | x 52.8 / 452.8 / 852.8，y 189，374.4×365 | `Outdoor Life name` `Editorial caption` `Editorial purpose`；`BuyeReviews name` `Roundup …`；`KOL name` `KOL …` |
| 5 | 1–3 | 10 / 11 / 12 | x 52.8 / 351.2 / 649.6，y 191，279.2×292 | `Publisher 0/1/2`、`Type 0/1/2 caption`、`Type 0/1/2 purpose` |
| 5 | 4（Media Buyer） | 13（上）/ 14（下） | 948.0，y 191 h144.5；y 348 h135，宽 279.2 | `Publisher 3`、`Type 3 caption`、`Type 3 purpose` |

图片 contain 适配、水平居中、顶对齐、原字节嵌入；`crop: [左, 上, 右, 下]` 为可见裁切比例（只裁空白边、导航栏或多余卡片，不改字节）。第 4 页任一槽可用 `pair`（两张并排：第一张按高度 `height`（默认 365）定宽、钉在槽左缘，第二张填满剩余宽度，间距 10），适合“TikTok 竖屏 + Instagram 方图”这类组合。

## 配置示例（节选）

```json
"media_pages": {
  "slide4": {
    "eyebrow": "内容媒体 · 礼物指南 · 亲子创作者",
    "title": "联盟伙伴推广形式示例（儿童玩具与 DIY 品类）",
    "subtitle": "以下为……公开推广内容示例，供了解合作方式，并非前述案例品牌的推广记录。",
    "footer": "截图为公开网页示例，2026-11 截取；不代表与上述媒体的合作承诺。",
    "slots": [
      {"image": "媒体_ApartmentTherapy_测评.png", "name": "Apartment Therapy", "caption": "家居生活媒体｜单品测评与购买推荐", "purpose": "…"},
      {"image": "媒体_AlmostMakesPerfect.png", "name": "Almost Makes Perfect", "caption": "亲子生活博客｜节日礼物指南与购买入口", "purpose": "…"},
      {"name": "亲子 KOL 创作者 · TikTok / Instagram", "caption": "…", "purpose": "…", "image": "媒体_TikTok.png",
       "pair": [{"image": "媒体_TikTok.png", "crop": [0.46, 0, 0.08, 0], "height": 320}, {"image": "媒体_Instagram.png"}]}
    ],
    "notes": "来源、原文件名→识别结果、裁切说明、不代表合作承诺"
  },
  "slide5": {
    "slots": [ {"image": "…Slickdeals…", "name": "Slickdeals", "caption": ["折扣 Deal 社区｜", "优惠曝光与购买讨论"], "purpose": "…"}, … ],
    "slot4": {"name": "Media Buyer · Google 搜索广告", "caption": ["Media Buyer｜", "付费引流与榜单推荐"], "purpose": "…",
              "images": [{"image": "…搜索广告.png"}, {"image": "…落地页.png", "crop": [0, 0, 0, 0.5]}]},
    "summary": ["通过 Levanta，卖家可连接……多类型联盟伙伴，", "组合……等推广方式，拓展产品曝光与销售机会。"]
  }
}
```

## 品类示例库（`assets/media-library/`）

做过的品类把截图和配好的 `media_pages.json` 存成一个包，之后同品类直接引用，不用再找图：

```
assets/media-library/
├── 家居安防类/        6 张（保险箱/枪柜：Gun University、SafesRight、Outdoor Life·YouTube、Slickdeals、SafeWise、Pew Pew Tactical）
└── 儿童玩具与DIY类/   10 张（Apartment Therapy、Almost Makes Perfect、TikTok+Instagram、Slickdeals、CNN Underscored、The Toy Insider、Google 广告+BuyBetter）+ strategy.example.json
```

用法：case-config.json 写 `"media_library": "家居安防类"`，`build.py` 读取该包的 `media_pages.json`，把图复制进 case 的 `sources/`。要微调文字就把包里的 JSON 复制到 `media_pages` 字段再改（`media_pages` 优先）。

新增一个品类包：建文件夹 → 放缩放到最长边 1600px 的 PNG → 写 `media_pages.json`（照上面示例） → 写 `README.md`（每张图的站点、页面标题、截取日期、裁切说明、“不代表合作承诺”）。相近品类可以借用（如“户外灯具”可借“家居安防”的 Deal/Media Buyer 栏），但标题要写“（××品类为主）”并在页脚注明哪些栏是其他品类示例。

## 规则

- **识别与命名**：用户的截图通常不按约定命名，逐张打开识别；站名按截图可见名称写（页眉 Logo、频道名、账号名），看不出的用用户提供的名称，仍看不出用泛称（如“亲子生活博客 · 礼物指南”）并在备注写明。创作者账号写“名称 · 平台”。
- **类型归位**：第 4 页放内容型（垂类/生活媒体测评、榜单/礼物指南、创作者），第 5 页放促销与引流型（Deal 社区、综合媒体导购、Newsletter、Media Buyer）。用户没给某一类截图时：优先保留模板原图并在页脚注明“××一栏为跨类目示例”（`slots` 里该位置写 `null` 或 `{"keep": true}`，脚本就跳过这一栏不动），或用同品类另一张顶位并在备注写清（如用 YouTube 顶 Newsletter）。
- **标题与副标题**：全部换成该品类图时写“（××品类）”；仍含模板图时写“（××品类为主）”并在副标题点名哪一栏是跨类目。
- **只做可见裁切**，原字节不动；裁切比例写进备注与 picture-fit.json。
- **事实边界**：截图是公开页面的推广形式示例，不写成案例品牌或目标客户的推广记录，不暗示这些媒体已与 Levanta 或客户合作；Media Buyer 不把域名等同于某一 Levanta 公司主体，不作投放业绩主张。
- **大截图**：单张 >1.5MB 的 PNG 在某些上传通道会超时；先压成 JPG/缩小一半再放进 `sources/`（页面展示尺寸最多 374px 宽，无需原始分辨率）。
- 渲染后检查：每栏图不变形、栏标题两行内、页脚单行；`validate.py --original` 通过。
