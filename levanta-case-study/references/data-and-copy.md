# 数据口径与结论文案

## 数据底稿

每品牌保留：标签、用户给定产品、站点、币种、起止日期、Sales、Conversions、Commission、BRB及其来源、归因渠道、两张截图路径。对金额保留原始小数，不从显示整数反推。

| 表格项 | 计算/含义 |
|---|---|
| 归因销售额 Sales | 当前报告原值；不是品牌全部Amazon销售额或已证实的因果增量 |
| 转化量 Conversions | 忠实保留报表指标；不要未经确认改称订单数或销量件数 |
| 平均客单价 | Sales ÷ Conversions，沿用该指标名称并显式给出公式 |
| 联盟佣金 Commission | 当前报告原值 |
| 平均佣金率 | Commission ÷ Sales |
| BRB费用抵扣 | 报表实际值或用户最新明确补充值 |
| 净佣金成本 | Commission − BRB |
| 渠道ROAS | Sales ÷（Commission − BRB） |
| 净佣金成本率（类ACOS） | （Commission − BRB）÷ Sales，百分比；与同口径ROAS互为倒数 |

例：净成本率0.1253显示12.53%，不是0.13%。金额显示整数带千位分隔，比例和ROAS保留两位小数。品牌数据币种、日期和归因范围不同，不随意合计或横向排名。

零分母显示“—”并解释原因；缺失BRB保留未知状态。净佣金为零或负值时不展示“无限ROAS”或称“免费获客”，先核对来源和适用范围。高ROAS或低类ACOS本身不证明盈利。

## 计算脚本

脚本仅依赖 Python 3 标准库（`make_case.py` 会自动调用；单独运行时）：

```bash
python3 scripts/calculate_metrics.py <case>/input.json --output <case>/metrics.json
```

输入结构如下，**数字仅为计算演示，不能作案例事实**：

```json
{
  "currency": "USD",
  "brands": [
    {"label": "品牌 A", "sales": "1000.00", "commission": "150.00", "conversions": 50, "brb": "100.00"}
  ]
}
```

金额建议用字符串保留精度。`brb` 可省略或为null以表示未知，显式0表示已确认零值。全局币种必填；可选品牌币种必须与全局一致。脚本输出原始计算和显示字符串，不审核渠道或政策资格。

## BRB 与类 ACOS

- BRB是合格销售对应的费用抵扣，不是固定现金返佣，也不是全部Levanta销售额的固定10%。在提到政策时，使用“合格 Amazon Attribution 归因销售额平均约10%提供费用抵扣”。美国站、参与计划、品牌资格、品类差异和实际抵扣集中放简短注脚。
- 案例中存在Creator Connections时，不把其销售额也乘10%估算实际BRB。不适用情形按用户明确情况或已核实规则处理。
- “类ACOS”是类比标签，实质为净佣金成本率，不是Amazon Ads后台原生ACOS，也不包含平台费、抽佣、付费合作等未纳入成本。若用户要求全费用ROI，另明确费用分母并调整指标名称，不能偷换本表口径。
- 推荐注脚：“类 ACOS＝（Commission − BRB）÷ Sales，将净佣金成本换算为销售额占比以便直观类比；ROAS与类ACOS均未计平台费等其他合作费用。”
- 政策和定义再次用于新案例时核对当前官方来源，不把参考案例的查询日期当本次验证日期。

官方核查入口：

- [Amazon BRB](https://sellercentral.amazon.com/help/hub/reference/external/GL9HPJ34VBFP76HX)
- [BRB与Amazon Attribution](https://advertising.amazon.com/resources/whats-new/brand-referral-bonus-amazon-attribution)
- [Amazon ACOS定义](https://advertising.amazon.com/library/guides/acos-advertising-cost-of-sales)

## 结论的写法

结论解释客户能理解的合作价值，避免重复表格或变成伙伴流水账。正文各条约1–2行，最多保留少量百分比，不展示逐家成交金额。

1. **出单伙伴**：按本次可见成交记录与已核实主体定位说明内容媒体、生活方式KOL创作者、榜单测评、折扣Deal等出单类型。大媒体名称要有本次成交记录；集团账号成交不可任意分摊到集团旗下某刊物。分类可能交叉，不当作互斥统计。
2. **佣金与BRB**：说明品牌佣金水平或合作策略差异及抵扣对净成本的作用。只有平均佣金率时，不能据此编造某品牌给不同伙伴设定私佣的具体策略。
3. **渠道效果**：根据本次实际结果评价归因销售、ROAS、类ACOS和合作潜力，不固定写“效果很好”“ROAS高”。可用“通过Levanta合作多类型联盟客，拓展销售来源”；不要把单期归因结果写成已证明新增销量或整个类目的效果保证。

可以优先突出creator/content，但不能为此把Deal、Coupon、Media Buyer重新贴成纯内容标签。只看到Top列表或局部截图时，不声称某类型占多数；确需占比时标明是“截图中可核实记录的下限”和准确分母。缺少份额证据可用“重要出单来源”，不写“主要依靠”。

以下是**原美妆个护案例经确认的语气示例**，媒体名称和结论必须随新案例改写：

> 内容媒体与生活方式 KOL 创作者是重要出单来源，BuzzFeed、People Inc.、NBCUniversal 等大媒体已有成交。榜单测评、折扣 Deal 类伙伴也有出单贡献，出单媒体类型多元。

不要因为用户举了CNN等熟悉媒体的例子，就写成这次案例真实出单媒体。没有出单依据的名字不进入案例结论。

## 数据合规

- 第 2 页截图默认打码（`redact_shots`），不得外发未打码版本。
- 结论与策略页点名合作方前先确认负责人口径；默认只写伙伴类型。可点名时只点有成交且身份明确的主体，不写单个伙伴金额。
- 面向特定客户时避免同细分类目、规模相近的品牌样本；小品类下精确数值本身就是指纹，必要时只给比例与区间。
