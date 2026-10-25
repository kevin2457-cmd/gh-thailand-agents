# MGT 409 — Final Project AI Prompts

**姓名：** Chirong Kevin Yang
**项目：** GH Thailand 仓储库存 + CRM 多 Agent 系统

> 说明：为保护客户隐私，下面引用的 prompt 原文里的客户微信名已替换为「客户A、客户B……」，其余内容未改。

本文件记录我在完成 Final Project 时向 vibe coder 实际输入的 prompt，每一步一节（按 `WORKFLOW.md` 的阶段编号）。每节包括：

1. 这一步做什么。
2. 我实际输入的首次 prompt。
3. 如果我提出了修改要求，记录实际的 follow-up prompt，并用一句话说明第一次结果哪里不足；如果没有，就写“无”。

---

## Step 1：骨架（仓库结构、SQLite 表结构、模拟数据、.env 读取）

**首次 prompt：**

> 好，今晚先把骨架搭好：仓库结构、SQLite 表结构、模拟数据、.env 读取。明天我检查。

**Follow-up prompt：** 待检查（明天）

---

## Step 2：导入真实数据（采购 Excel）

**首次 prompt：**

> 所有的采购excel都放进去了，是真实的数据

**Follow-up prompt（回答 Claude 关于采购 Excel 的问题）：** 第一次结果需要我补充 Excel 里没有的信息（日期、版本、单位、中文俗称）。

> 股东分成不导入：是的。
> agent 必须得能识别中文，转换成英文，不然的话统计不了。
> 4 月按"内部"。
> 除了 10 月的都到货了，你就按照之前每 2 个月发一个到一个来计算吧。
> 第一柜按多的结算（洛杉矶货品清单）。
> 当量是桶/瓶的个数，价格是美元。
> 紫粉 Monster Bloom，香味 Floralicious，棉花糖 Bud Candy，鸦片粉 Weight Max，Original 就叫 Original。其他你不懂的中文全部跟我 check。

**Follow-up prompt 2（确认产品名映射）：** 第一次导入有几个产品名不确定是不是同一个产品，需要我确认。

> 第一柜全部按洛杉矶清单算：没问题。
> GH-Micro-25lb 是 typo，就是 Core。如果你愿意可以给我一个文件夹，我把实际的图片发给你参照。
> Koolbloom 有液体和粉末两种，看体积参数，lb 是粉，Gal 是液体。
> PH UP = PH UP Advance，PH Down = PH Down Advance：对的。
> Green J - 1L = Green Juice，Cal Mg = Cal Mg Plus：对的。
> 2025 年 2 月到 11 月之间的货柜文件找不到了。
> Terpinator 按洛杉矶批发价 + 10 估拿货价、售价按到岸成本 × 1.5：没问题。

**Follow-up prompt 3（最后两个规格）：** 还有两个产品在 Excel 里没写规格。

> 2 月和 4 月表里的 Koolbloom 是 6gal。
> CloneX 都是 1L 的。

**Follow-up prompt 4（产品照片）：** 销售报告和盘点里有很多中文俗称和 Excel 里没有的产品，需要用实物照片对照。

> 放进去了，缺失的图片你列清单给我我全部补充。

**Follow-up prompt 5（盘点表）：** 盘点表里有分隔线、同名产品出现两次、Excel 里没有的产品，需要我说明。

> 分隔线不是不同仓库，都是一个仓库。
> 同名产品合并总数就可以，同样名字的都是同规格。
> Big time enzyme、Silica blast、Diamond nectar、True flo、Bloom liquid plant food、CYCO silica 5gal、Weight Max 10kg 是早期货柜（缺失的那段文件）进的货：对的。
> 采购 Excel 里有、但盘点里没出现的（Pro Grow、Pro Bloom、Balance、GH Grow、Late）：对啊卖完了，卖很快。

**Follow-up prompt 6（规格和俗称）：** 照片和盘点表里的规格不一致，还有认不出的俗称。

> 三朵花也是 Monster Bloom 的别名。
> 图片只是表明品牌和名字，实际规格按我们 Excel 的。实际上我们绝大多数都是卖最大规格，除了 CloneX 以外。
> Bio root 都是一个规格 6gal；Cal mag 都是 6gal；Overdrive 都是 6gal。
> Floralicious：6gal 的 8 个，1gal 的 24 个，2.5gal 的我们没有。

**Follow-up prompt 7（俗称确认）：** Claude 根据照片猜了几个俗称，需要我确认。

> 客户名：等一下继续问我。
> 三色粉的红/绿/黑/花 = FloraPro Bloom / Grow / Calcium+Micros / Late Bloom：正确！
> Cyco 糖是 Supa Stiky：对；番茄是 Cal-Mag：对；向日葵是 Floralicious。
> Bush load：你把没有图片的都发个清单给我，我做给你，然后弹出我放在哪里。

**Follow-up prompt 8（补充产品照片）：** 有 12 个产品没有照片，Claude 认不出 Bush load。

> FloraBloom 30 包（80 美元一包）是 FloraPro Bloom 25lb：没错！
> 图片我放进去了个 pdf，你看一下。

**Follow-up prompt 9（客户名）：** 销售报告里没有客户名，沉睡客户功能需要知道每一单是谁买的。

> 这个还是需要看截图了，你创造一个新的文件夹吧弹出来。
> 放进去了 8 个图片。

**Follow-up prompt 10（截图订单确认）：** Claude 从截图里找到报告漏记的订单和算错的地方，需要我确认。

> 客户C 9.3 "先发一个 bioroot + 一个 sticky"：都发了最后。
> 客户B 10.5 绿色粉写 5 包、算式 120×3：完蛋了少收钱了……是 5。
> 客户G 30000 泰铢：10 个 CloneX。
> 前面的客户我没时间一一写了，你按顺序编排一下吧，以后都会录入的。

**Follow-up prompt 11：**

> 客户E 的"香味 5G"是 6gal：是的。
> 6.25 第 5 单是客户B：对的。
> 客户F那单是哪一天：图片没有日期码？10/17。

---

## Step 3：Agent 核心

**首次 prompt：**

> 客户F那单用 10/19，开始做 agent 核心。

（上一轮我选的按钮内容：先用真实产品目录重做模拟数据，然后录单 agent 把文字订单解析成待审批记录（含算式校验），分析 agent 做补货和沉睡客户，老板审批后才写入，记审计日志和 token。）

**Follow-up prompt：** 无
