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

**Follow-up prompt：** 第一次冒烟测试里，录单 agent 按算式把绿色粉记成 3 包（真实是 5 包），校验也把折前小计误报为算错，Claude 自己修正了提示词和校验规则。

> "根水"= BioRoot：对的。
> 测试用的订单照客户B那单写、会进 GitHub：不介意。

---

## Step 4：前端（Dash）

**首次 prompt：**

> 前端按你推荐（Dash：纯 Python，python app.py 一个命令就能启动）。

**Follow-up prompt：** 无（中途问了一句"我们这个有前端吗？"）

---

## Step 5–10：真实数据导入、Safety、Tokenomics、报告、幻灯片、交付

**首次 prompt：**

> 今天就做完吧，

**Follow-up prompt：** 中途问"还需要什么？"（Claude 列了只有我能提供的基线数字、竞品、真实使用、GitHub）。真实使用时发现录单页没有日期栏：

> 录入这里貌似没有日期

> ok我马上开始。但是先不提交，我想看一下所有东西。https://github.com/Kevinyang2457/gh-thailand-agents.git

> 报告里的业务数字和我记录里的 3 个错误公开：可以 / 没问题。真实使用的感受：我写好了。

> https://zlisto.github.io/mgt_409_fa26/project_requirements.html 你确定一下所有打分标准都用上了吗？操作界面是否给老师提交一个英文版的？

> 确定都搞好了？能拿到高分么，这是我的final作业

> 我的员工就在我边上，我们可以做一个员工的吗？（员工试用后反馈：有重复录单的风险；年月日应该做一个下拉。Claude 当晚加了重复检测和日期下拉框。）

> SO-000042 和 6.30 那单一样：这是模拟的日期。SO-000043 拒绝是因为同时递交了两个一样的订单，重复了。6.25 第 1、3 单：这个是真的下单的一样，碰巧。
> 我希望我的页面有一些 cannabis 元素，我希望是绿色白色的设计。

> 底色换米色吧，这样纯白色没有边框了看着很不好看
> 先别推，我还想改一些地方。

---

## Step 11：老板提出的新功能（支付凭证、库存搜索、销售统计）

**首次 prompt：**

> 录入订单这里，我希望加一个支付凭证的上传。可以接受转账的截图，如果客户给的是现金就需要老板审批。然后我希望库存设计一个搜索产品的库存这样。我希望在大目录上，加一个销售统计，我这些金额没体现，我系有一个统计全年，本月，本周，本日的销售订单，显示泰铢和美金的收入的。这样我才知道账上有多少钱

**Follow-up prompt：** 中途改设计：

> 颜色还是对比度太低了，不然改成黑金吧，黑色+金字+金色大麻叶点缀

> 销售统计这里，未付款的也单独列一个出来

> （截图：按付款方式的表全是 0）这一块为啥都是0，怎么调整都是0，想表达什么？然后客户那里我想有个可以编辑的，就哪怕已经录入的，我可能希望给他们建档案，名字、地址、购买习惯

> 设计这里不用再改了。现在销售统计那里给我一个能选择两个日期然后看其中卖了多少的这么一个功能。然后录入这里如果选择未付款，应该在审批这里标红，审批能通过的原则也是要么上传支付凭证（一个或者多个照片）或者选择现金。

> 跟我说话一律说中文，然后客户那里再加一个统计，累计消费金额

> 深蓝色提示词看不见，换金色吧。然后CUST-004 和 CUST-007（真实客户名已隐去）为什么没有购买金额

> （截图：多选框里还有蓝色字）还是有蓝色的提示字，全部换金色的不然看不见！

> 遇到了一个新的SKU，叫IPM，是一个Athena品牌的杀虫剂，可以加上去吗？否则我也没办法录入（5G；售价18000泰铢，底价14400泰铢；就叫 IPM；库存先记 0）

> 最后确认一下，是否满足老师所有要求，https://zlisto.github.io/mgt_409_fa26/project_requirements.html。都满足了就提交了

> 用老账户（推送到 kevin2457-cmd 下新建的仓库）
