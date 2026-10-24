# MGT 409 — Final Project AI Prompts

**姓名：** Chirong Kevin Yang
**项目：** GH Thailand 仓储库存 + CRM 多 Agent 系统

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
