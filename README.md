# levanta-case-study

用 Levanta 后台截图制作中文品牌案例 PPTX/PDF 的 Claude skill（团队版）。默认八页：品牌数据对比 → 后台截图证据 → 推广成本与效果测算 → 两页联盟伙伴推广形式示例 → 站外媒体组合策略页 → 卖家常见问题钩子页 → 联系与演示邀请页。

## 安装

- **Claude.ai / Claude 桌面版**：下载 [`dist/levanta-case-study.skill`](dist/levanta-case-study.skill)，在 Claude 的 Skills 设置里上传即可。
- **Claude Code**：把 `levanta-case-study/` 文件夹复制到项目的 `.claude/skills/` 下（或个人的 `~/.claude/skills/`）。

## 数据合规

后台截图在生成时默认打码（KPI 数值、创作者名称、金额），页面文字默认只写伙伴类型；详见 `levanta-case-study/SKILL.md`“数据合规”。成品文件不要放进公开仓库或公开群。

## 使用前准备

读 [`levanta-case-study/references/input-checklist.md`](levanta-case-study/references/input-checklist.md)：哪些材料必须提供（品类、三品牌各两张后台截图、产品名、BRB 情况、**发送人自己的联系信息和二维码**），哪些按情况提供（品类媒体截图、客户名……），哪些是模板固定不能改的。

## 目录

```
levanta-case-study/
├── SKILL.md                 技能说明（AI 读）
├── assets/                  六页模板 reference.pptx、Logo、默认配置、品类媒体示例库
├── scripts/                 make_case.py 一键流水线及各页模块
└── references/              数据口径、版式、各页细则、输入清单、配置字段
dist/levanta-case-study.skill   打包好的安装文件

```


## 更新

模板、脚本或示例库有改动时：改 `levanta-case-study/` 下的文件 → 重新打包（skill-creator 的 `package_skill.py`，或把文件夹 zip 后改名 `.skill`）→ 覆盖 `dist/`。品类媒体示例库在 `assets/media-library/`，每做一个新品类加一个文件夹（格式见其中 README）。

## 更新记录

- **v1.5（2026-11-10）**：数据合规——后台截图默认打码（`redact_shots`），模板第 1–2 页改为占位数据与已打码截图，成品示例 PDF 下架，SKILL.md 新增“数据合规”一节。
- **v1.4（2026-11-10）**：跨品类合集版支持——`overview.json` 额外表格页（多品类案例速览）、`period_words` / `slide2_subtitle_override`，新增跨品类合集成品示例。
- **v1.3（2026-11-09）**：新增厨具类媒体示例库（8 张，七栏齐全）与厨具类成品示例。
- **v1.2（2026-11-09）**：第 4–5 页换图支持单栏保留模板图（`slots` 里写 `null` 或 `{"keep": true}`）；策略页单元格支持数组强制换行，避免英文媒体名在词中间折行。
- **v1.1（2026-11-09）**：加入品类媒体示例库（家居安防类、儿童玩具与DIY类）。
