# 运行环境与工具

脚本全部是 Python 3，依赖：

| 依赖 | 用途 | 没有时 |
|---|---|---|
| `python-pptx`、`Pillow` | 读写 PPTX、量图 | 必需：`pip install python-pptx pillow` |
| LibreOffice（`soffice`） | PPTX → PDF、渲染检查 | 只输出 PPTX，PDF 在本机 PowerPoint/Keynote 另存；页面检查改为打开 PPTX 目视 |
| `pdftoppm`（poppler） | 把 PDF 渲染成逐页 JPG 供 AI 目视检查 | 跳过渲染，用 PDF 预览 |
| `opencv-python`、`numpy` | 二维码一致性比对 | QA 跳过该项（validation.json 里标 skipped），发送前人工扫码确认 |

在 Claude.ai / Claude Code / Cowork 里：把 skill 解压后的目录当作 `<skill_root>`，为每个案例建一个 case 目录（结构见 `config-reference.md`），把用户上传的截图放进 `sources/`，然后：

```bash
python3 <skill_root>/scripts/make_case.py --case <case_dir>
```

渲染出来的 `out/render/page-N.jpg` 要逐页看一遍（重点：第 1 页结论三条是否单行、第 2 页产品标签、第 4–5 页栏标题、策略页表格、钩子页六问、联系页职称行）。LibreOffice 的回退字体比 PowerPoint 的宽，渲染里不换行，PowerPoint 里就不会换行。

字体：模板用 Arial Unicode MS；导出环境缺字时 LibreOffice 会回退到可用的 CJK 字体，这不影响 PPTX 本身。如果渲染出现方块，说明环境没有任何 CJK 字体，需要安装（如 Noto Sans CJK）再导 PDF。

不要做的事：不从空白模板重画版式；不用 PNG 预览冒充可编辑 PPT；不修改 `assets/reference.pptx` 原件；不打开二维码里的链接。
