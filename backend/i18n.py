"""界面文字（English / 中文）和校验信息的英文翻译。

界面默认英文（老师和新用户），老板用 ?lang=zh 看中文。
校验信息在数据库里按中文原文保存（老板看的就是原文）；英文界面显示时按下面的规则翻译。
"""
from __future__ import annotations

import re

TEXT: dict[str, dict[str, str]] = {
    "title": {"en": "GH Thailand · Inventory + CRM Agents", "zh": "GH Thailand · 库存 + CRM Agents"},
    "subtitle": {"en": "Chat orders into a database: order entry, approval, reorder, customer follow-up",
                 "zh": "聊天记录变成数据库：录单、审批、补货、客户跟进"},
    "sample_data": {"en": "Sample data", "zh": "模拟数据"},
    "real_data": {"en": "Real data", "zh": "真实数据"},
    "today": {"en": "Today", "zh": "今天"},
    "role": {"en": "Role:", "zh": "当前角色："},
    "owner_role": {"en": "Owner (approves)", "zh": "老板（审批）"},
    "staff_role": {"en": "Staff (enters orders)", "zh": "员工（录单）"},
    "owner": {"en": "Owner", "zh": "老板"},
    "staff": {"en": "Staff", "zh": "员工"},
    "tab_ask": {"en": "Ask", "zh": "问答"},
    "tab_intake": {"en": "Order entry", "zh": "录单"},
    "tab_approvals": {"en": "Approvals", "zh": "审批队列"},
    "tab_inventory": {"en": "Inventory & reorder", "zh": "库存与补货"},
    "tab_customers": {"en": "Customers", "zh": "客户"},
    "tab_usage": {"en": "Usage & audit", "zh": "用量与审计"},
    # chat
    "chat_h": {"en": "Ask the owner's assistant (orchestrator → inventory agent / CRM agent)",
               "zh": "问老板助手（协调 agent → 库存 agent / CRM agent）"},
    "chat_ph": {"en": "Ask about stock, reorders, customers… (Enter to send)", "zh": "问库存、补货、客户……（回车发送）"},
    "send": {"en": "Send", "zh": "发送"},
    "chat_hello": {"en": "Hi! Ask me about stock, reorders or customers — or click an example question above.",
                   "zh": "你好！可以问我库存、补货、客户的问题。上面有示例问题。"},
    "thinking": {"en": "Thinking", "zh": "思考中"},
    "error": {"en": "Error", "zh": "出错了"},
    "tools_used": {"en": "Tools used · {n} calls", "zh": "Tools used · {n} 次调用"},
    "usage_line": {"en": "{req} model requests ({per}) · input {inp:,} (cached {cached:,}) · output {out:,} · ${cost:.5f}",
                   "zh": "{req} 次模型请求（{per}）· 输入 {inp:,}（缓存 {cached:,}）· 输出 {out:,} · ${cost:.5f}"},
    # intake
    "intake_h": {"en": "Order entry (intake agent → code checks → approval queue)",
                 "zh": "录单（录单 agent 解析 → 代码校验 → 待审批）"},
    "customer_l": {"en": "Customer (the name stays on this computer; the model only sees a code)",
                   "zh": "客户（名字只存在本机，不发给模型）"},
    "customer_ph": {"en": "Choose a customer…", "zh": "选择客户…"},
    "new_customer_ph": {"en": "…or type a new customer name (e.g. the WeChat group name)",
                        "zh": "或者输入新客户名字（例如微信群名）"},
    "date_l": {"en": "Order date (used when the text has no date; type to search, e.g. 09-29)",
               "zh": "订单日期（文字里没写日期时用这个；可以打字搜索，例如 09-29）"},
    "source_l": {"en": "Source", "zh": "来源"},
    "src_wechat": {"en": "WeChat chat", "zh": "微信聊天"},
    "src_excel": {"en": "Excel", "zh": "Excel"},
    "src_report": {"en": "Sales report", "zh": "销售报告"},
    "src_chat": {"en": "Other", "zh": "其他"},
    "text_l": {"en": "Order text (paste straight from WeChat / Excel / the sales report — any language)",
               "zh": "订单文字（从微信 / Excel / 报告直接粘贴）"},
    "text_ph": {"en": "Paste one order…", "zh": "粘贴一张订单……"},
    "submit": {"en": "Parse & submit for approval", "zh": "解析并提交审批"},
    "examples": {"en": "Examples:", "zh": "示例："},
    "ex_normal": {"en": "Normal order", "zh": "正常订单"},
    "ex_math": {"en": "Order with a math error", "zh": "算错的订单"},
    "ex_attack": {"en": "Order with an attack", "zh": "带攻击的订单"},
    "result_h": {"en": "Result", "zh": "解析结果"},
    "result_empty": {"en": "After you submit, the parsed lines, warnings and token usage appear here.",
                     "zh": "提交后在这里显示解析结果、警告和 token 用量。"},
    "col_text": {"en": "Text", "zh": "原文"}, "col_sku": {"en": "Standard SKU", "zh": "标准 SKU"},
    "col_qty": {"en": "Qty", "zh": "数量"}, "col_price": {"en": "Unit price", "zh": "单价"},
    "col_disc": {"en": "Discount", "zh": "折扣"}, "col_net": {"en": "Net USD / unit", "zh": "实收/件 USD"},
    "candidates": {"en": "Candidates: ", "zh": "候选："}, "unknown": {"en": "Unknown", "zh": "不认识"},
    "submitted": {"en": "Submitted for approval #{pid} · order date {d}", "zh": "已提交待审批 #{pid} · 订单日期 {d}"},
    "must_fix_intake": {"en": "Must be resolved first (the owner does this in Approvals):",
                        "zh": "必须先处理（老板在审批队列里处理）："},
    "warnings_h": {"en": "Please note:", "zh": "需要注意："},
    "all_ok": {"en": "All checks passed.", "zh": "校验通过，没有发现问题。"},
    "sent_to_model": {"en": "Text sent to the model (redacted)", "zh": "发给模型的文字（已脱敏）"},
    "need_text": {"en": "Please paste the order text first.", "zh": "请先粘贴订单文字。"},
    "date_future": {"en": "The order date cannot be in the future.", "zh": "订单日期不能在未来。"},
    "date_format": {"en": "Write the order date as 2026-10-20.", "zh": "订单日期格式要写成 2026-10-20。"},
    "need_customer": {"en": "Please choose a customer.", "zh": "请选择客户。"},
    "unlabeled": {"en": "Unlabeled customer (historical orders)", "zh": "未标注客户（历史订单）"},
    "unlabeled_short": {"en": "Unlabeled customer", "zh": "未标注客户"},
    # approvals
    "pick_sku": {"en": "Choose SKU", "zh": "选择 SKU"}, "set": {"en": "Set", "zh": "确定"},
    "submitted_by": {"en": "submitted by {who} · source {src} · {ts}", "zh": "{who}提交 · 来源 {src} · {ts}"},
    "must_fix": {"en": "Must be resolved first:", "zh": "必须先处理："},
    "note_h": {"en": "Note:", "zh": "注意："},
    "orig_text": {"en": "Original order text (redacted)", "zh": "原始订单文字（已脱敏）"},
    "approve": {"en": "Approve & write", "zh": "批准写入"}, "reject": {"en": "Reject", "zh": "拒绝"},
    "only_owner": {"en": "Only the owner can approve.", "zh": "只有老板可以批准。"},
    "pending_h": {"en": "Pending approval ({n})", "zh": "待审批（{n}）"},
    "pending_intro": {"en": "Orders submitted by staff wait here. Only after the owner approves are they written to the "
                            "database and stock is moved; every step is in the audit log.",
                      "zh": "员工提交的订单先放在这里。老板批准之后才写进数据库、扣库存；每一步都记审计日志。"},
    "approve_clean": {"en": "Approve all clean orders ({n})", "zh": "批准所有干净的订单（{n}）"},
    "approve_clean_note": {"en": "Only orders with no warnings at all; yellow or red ones must be reviewed one by one.",
                           "zh": "只包括没有任何警告的订单；有黄色或红色提示的要逐单看。"},
    "no_pending": {"en": "Nothing waiting for approval.", "zh": "没有待审批的订单。"},
    "recent_h": {"en": "Recently processed", "zh": "最近处理"},
    "col_customer": {"en": "Customer", "zh": "客户"}, "col_result": {"en": "Result", "zh": "结果"},
    "col_sale": {"en": "Sale", "zh": "销售单"}, "col_reviewed": {"en": "Reviewed", "zh": "审批时间"},
    "col_note": {"en": "Note", "zh": "备注"},
    "approved": {"en": "Approved", "zh": "已批准"}, "rejected": {"en": "Rejected", "zh": "已拒绝"},
    "msg_clean": {"en": "Approved {n} clean orders; stock updated.", "zh": "已批准 {n} 单干净的订单，库存已更新。"},
    "msg_approved": {"en": "#{pid} approved → sale {sale}; stock updated.", "zh": "#{pid} 已批准，写入销售单 {sale}，库存已更新。"},
    "msg_rejected": {"en": "#{pid} rejected.", "zh": "#{pid} 已拒绝。"},
    "msg_pick_first": {"en": "Choose a SKU in the dropdown first.", "zh": "请先在下拉框里选一个 SKU。"},
    "msg_set": {"en": "#{pid} line {line} set to {sku}.", "zh": "#{pid} 第 {line} 行已设为 {sku}。"},
    # inventory
    "inv_h": {"en": "Reorder plan (deterministic formula, not an AI guess)", "zh": "补货建议（确定性公式，不是 AI 猜的）"},
    "inv_formula": {"en": "Daily rate = units sold in the last 120 days / 120; days of cover = (on hand + in transit − safety "
                          "stock) / daily rate; latest order date = today + days of cover − 60-day lead time.",
                    "zh": "日均销量 = 最近 120 天销量 / 120；可用天数 = (现有 + 在途 − 安全库存) / 日均销量；"
                          "最晚下单日 = 今天 + 可用天数 − 交期 60 天。"},
    "kpi_onhand": {"en": "On hand (buckets/bags)", "zh": "现有库存（桶/包）"},
    "kpi_transit": {"en": "In transit", "zh": "在途"},
    "kpi_urgent": {"en": "Out of stock / order now", "zh": "已断货 / 马上下单"},
    "kpi_sold": {"en": "Products sold in the last 120 days", "zh": "近 120 天有销量的产品"},
    "c_status": {"en": "Status", "zh": "状态"}, "c_product": {"en": "Product", "zh": "产品"},
    "c_onhand": {"en": "On hand", "zh": "现有"}, "c_transit": {"en": "In transit", "zh": "在途"},
    "c_arrival": {"en": "Next arrival", "zh": "下批到货"}, "c_rate": {"en": "Daily rate", "zh": "日均销量"},
    "c_safety": {"en": "Safety stock", "zh": "安全库存"}, "c_cover": {"en": "Days of cover", "zh": "可用天数"},
    "c_orderby": {"en": "Order by", "zh": "最晚下单日"},
    "stockout_flag": {"en": "Out before arrival", "zh": "到货前会断货"},
    "st_out_of_stock": {"en": "Out of stock", "zh": "已断货"}, "st_order_now": {"en": "Order now", "zh": "马上下单"},
    "st_order_soon": {"en": "Order soon", "zh": "尽快下单"}, "st_ok": {"en": "OK", "zh": "充足"},
    "st_no_recent_sales": {"en": "No recent sales", "zh": "近期无销量"},
    # customers
    "dormant_h": {"en": "Dormant customers ({n})", "zh": "沉睡客户（{n}）"},
    "dormant_rule": {"en": "Rule: at least 2 orders, and silent for more than 2× their usual gap between orders.",
                     "zh": "规则：至少 2 单，距上次下单超过平时下单间隔的 2 倍。"},
    "c_orders": {"en": "Orders", "zh": "订单数"}, "c_gap": {"en": "Usual gap (days)", "zh": "平均间隔（天）"},
    "c_silent": {"en": "Silent for", "zh": "已多久没下单"}, "c_overdue": {"en": "Overdue ×", "zh": "超期倍数"},
    "c_usual": {"en": "Usually buys", "zh": "常买"}, "days": {"en": "{n} days", "zh": "{n} 天"},
    "followup_btn": {"en": "Draft follow-up", "zh": "写跟进话术"},
    "no_dormant": {"en": "No dormant customers right now.", "zh": "暂时没有沉睡客户。"},
    "all_customers_h": {"en": "All customers ({n})", "zh": "全部客户（{n}）"},
    "c_region": {"en": "Region", "zh": "地区"}, "c_last": {"en": "Last order", "zh": "最近下单"},
    "followup_h": {"en": "Follow-up message (CRM agent)", "zh": "跟进话术（CRM agent）"},
    "followup_hint": {"en": "Click “Draft follow-up” in the table above.", "zh": "点上表里的「写跟进话术」。"},
    "followup_q": {"en": "Write a short WeChat follow-up message (in Chinese) for customer {code}, mentioning the products "
                         "they usually buy. Explain it to me in English in one line.",
                   "zh": "给客户 {code} 写一条微信跟进话术，提到他常买的产品。"},
    # usage
    "runs_h": {"en": "By run type (measured, gpt-6-luna)", "zh": "按运行类型（实测，gpt-6-luna）"},
    "u_type": {"en": "Type", "zh": "类型"}, "u_runs": {"en": "Runs", "zh": "运行次数"},
    "u_req": {"en": "Model requests", "zh": "模型请求"}, "u_in": {"en": "Input tokens", "zh": "输入 token"},
    "u_cached": {"en": "Cached", "zh": "其中缓存"}, "u_out": {"en": "Output tokens", "zh": "输出 token"},
    "u_cost": {"en": "Total cost", "zh": "总费用"}, "u_avg": {"en": "Avg per run", "zh": "平均每次"},
    "kind_intake": {"en": "Order entry", "zh": "录单"}, "kind_ask": {"en": "Q&A", "zh": "问答"},
    "no_runs": {"en": "No model calls yet.", "zh": "还没有模型调用。"},
    "by_agent_h": {"en": "By agent", "zh": "按 agent"}, "a_req": {"en": "Requests", "zh": "请求"},
    "a_in": {"en": "Input", "zh": "输入"}, "a_cached": {"en": "Cached", "zh": "缓存"}, "a_out": {"en": "Output", "zh": "输出"},
    "a_cost": {"en": "Cost", "zh": "费用"},
    "audit_h": {"en": "Audit log (latest 30)", "zh": "审计日志（最近 30 条）"},
    "l_time": {"en": "Time (UTC)", "zh": "时间（UTC）"}, "l_who": {"en": "Who", "zh": "谁"}, "l_role": {"en": "Role", "zh": "角色"},
    "l_action": {"en": "Action", "zh": "动作"}, "l_entity": {"en": "Object", "zh": "对象"}, "l_detail": {"en": "Detail", "zh": "详情"},
}

EXAMPLE_QUESTIONS = {
    "en": ["Which products need to be reordered now?", "Which regular customers have stopped ordering?",
           "What were the best sellers in the last 30 days?", "Draft a follow-up for the customer silent the longest"],
    "zh": ["哪些产品需要马上补货？", "哪些老客户很久没下单了？", "最近 30 天卖得最好的是什么？", "给最久没下单的客户写一条跟进话术"],
}


def t(lang: str, key: str, **kw) -> str:
    s = TEXT[key].get(lang) or TEXT[key]["en"]
    return s.format(**kw) if kw else s


# 校验 / 审批信息：中文原文 -> 英文（按顺序匹配第一条）
_RULES: list[tuple[re.Pattern, str]] = [(re.compile(p), r) for p, r in [
    (r"^订单没写日期，按今天 (\S+) 记录$", r"No date in the order text; recorded as today, \1"),
    (r"^订单日期 (\S+) 在未来$", r"Order date \1 is in the future"),
    (r"^订单日期 (.+) 不是有效日期$", r"Order date \1 is not a valid date"),
    (r"^没有解析出任何产品$", "No products were found in the order"),
    (r"^「(.+?)」是 agent 根据上下文判断为 (\S+)，请核对$", r"“\1” was mapped to \2 by the agent from context — please check"),
    (r"^「(.+?)」有歧义，可能是 (.+)，请选择规格$", r"“\1” is ambiguous: \2 — choose the size"),
    (r"^「(.+?)」不在产品目录里，请确认是什么产品$", r"“\1” is not in the product catalog — please identify it"),
    (r"^(\S+) 在同一单里出现了两次$", r"\1 appears twice in this order"),
    (r"^「(.+?)」数量 (\S+) 不合理$", r"“\1”: quantity \2 is not valid"),
    (r"^「(.+?)」数量 (\S+) 异常大，请核对$", r"“\1”: quantity \2 is unusually large — please check"),
    (r"^「(.+?)」折扣 (\S+) 不合理$", r"“\1”: discount \2 is not valid"),
    (r"^「(.+?)」没有单价$", r"“\1” has no unit price"),
    (r"^「(.+?)」没写币种$", r"“\1” has no currency"),
    (r"^「(.+?)」算式不对：(.+?)（折后 (.+?)），订单写的是 (.+)$",
     r"“\1” arithmetic does not match: \2 (after discount \3), but the order says \4"),
    (r"^「(.+?)」算式不对：(.+?)，订单写的是 (.+)$", r"“\1” arithmetic does not match: \2, but the order says \3"),
    (r"^「(.+?)」实收 (\S+)，低于底价 (\S+)$", r"“\1” net price \2 is below the floor price \3"),
    (r"^(\S+) 库存只有 (\S+)，这单要 (\S+)：请先核对库存或修改数量$",
     r"\1: only \2 in stock but this order needs \3 — check the stock or change the quantity"),
    (r"^总计不对：按明细算是 (.+?)，订单写的是 (.+)$", r"Total does not match: the lines add up to \1, but the order says \2"),
    (r"^订单文字里有试图指挥系统的语句（已忽略，需老板人工核对）：(.+)$",
     r"The order text contains instructions aimed at the system (ignored; the owner must review): \1"),
    (r"^录单 agent 的疑问：(.+)$", r"Intake agent question: \1"),
    (r"^订单文字里的日期是 (\S+)，录单时选的是 (\S+)：已按订单文字记录，请核对$",
     r"The order text says \1 but \2 was entered; recorded as \1 — please check"),
    (r"^疑似重复录单：和销售单 (\S+)（(\S+)，(\S+)）的客户、产品和数量完全一样$",
     r"Likely duplicate: same customer, products and quantities as sale \1 (\2, \3)"),
    (r"^疑似重复录单：和待审批 #(\d+)（(\S+)，(\S+)）的客户、产品和数量完全一样$",
     r"Likely duplicate: same customer, products and quantities as pending #\1 (\2, \3)"),
    (r"^可能重复：和销售单 (\S+)（(\S+)，(\S+)）的产品和数量完全一样，请确认不是同一单$",
     r"Possible duplicate: same products and quantities as sale \1 (\2, \3) — check it is not the same order"),
    (r"^可能重复：和待审批 #(\d+)（(\S+)，(\S+)）的产品和数量完全一样，请确认不是同一单$",
     r"Possible duplicate: same products and quantities as pending #\1 (\2, \3) — check it is not the same order"),
    (r"^只有老板可以批准写入$", "Only the owner can approve"),
    (r"^只有老板可以拒绝$", "Only the owner can reject"),
    (r"^只有老板可以修改待审批记录$", "Only the owner can edit pending records"),
    (r"^这条记录不在待审批状态$", "This record is no longer pending"),
    (r"^还有必须先处理的问题：(.+)$", r"There are still blocking issues: \1"),
    (r"^还有产品没有确定 SKU$", "Some products still have no SKU"),
    (r"^客户 (\S+) 不存在$", r"Customer \1 does not exist"),
    (r"^(\S+) 不在产品目录里$", r"\1 is not in the product catalog"),
]]
_INLINE = [("(模型服务商的内容安全过滤拦截了这段文字)", "(blocked by the model provider's content filter)"),
           ("[地址已移除]", "[address removed]"), ("[电话已移除]", "[phone removed]"), ("[网址已移除]", "[link removed]"),
           ("[邮箱已移除]", "[email removed]"), ("[账号已移除]", "[account removed]"),
           ("批量批准（无警告）", "Bulk-approved (no warnings)"), ("老板在审批队列拒绝", "Rejected by the owner")]


def tr(msg: str, lang: str) -> str:
    """把代码生成的中文信息翻译成英文（英文界面用）；中文界面原样返回。"""
    if lang != "en" or not msg:
        return msg
    for a, b in _INLINE:
        msg = msg.replace(a, b)
    if "；" in msg and msg.startswith("还有必须先处理的问题："):
        head, rest = msg.split("：", 1)
        return "There are still blocking issues: " + "; ".join(tr(x, lang) for x in rest.split("；"))
    for pat, rep in _RULES:
        if pat.match(msg):
            return pat.sub(rep, msg)
    return msg
