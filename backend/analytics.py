"""确定性业务计算：库存、补货、沉睡客户、客户历史、销量汇总。

这里的数字全部由代码算出，agent 只负责调用和解释，不自己做算术。
返回的数据里只有客户代号（code），没有客户名字、电话、地址。
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from statistics import mean

from backend.config import UNLABELED_CODE

RATE_WINDOW_DAYS = 120   # 日均销量看最近 120 天（真实销售数据从 6 月开始）
SAFETY_DAYS = 14         # 产品没设安全库存时，用 14 天销量作为安全库存
SOON_DAYS = 14           # "最晚下单日"在 14 天内 = 尽快下单
DORMANT_FACTOR = 2.0     # 超过平时下单间隔的 2 倍没下单 = 沉睡
MIN_ORDERS_FOR_CYCLE = 2  # 至少 2 单才能算下单间隔


def _d(s: str) -> date:
    return date.fromisoformat(s)


def stock_status(conn: sqlite3.Connection, sku: str | None = None) -> list[dict]:
    """每个 SKU 的当前库存、在途数量和下一批到货日期。"""
    sql = """SELECT s.sku, p.name, p.size, s.on_hand, p.safety_stock, p.lead_time_days,
                    COALESCE(t.in_transit, 0) AS in_transit, t.next_arrival
             FROM v_stock s JOIN products p ON p.sku = s.sku
             LEFT JOIN v_in_transit t ON t.sku = s.sku
             WHERE p.active = 1 AND (? IS NULL OR s.sku = ?)
             ORDER BY s.sku"""
    return [dict(r) for r in conn.execute(sql, (sku, sku))]


def daily_rates(conn: sqlite3.Connection, today: date, window: int = RATE_WINDOW_DAYS) -> dict[str, float]:
    since = (today - timedelta(days=window)).isoformat()
    rows = conn.execute(
        """SELECT si.sku, SUM(si.qty) AS q FROM sale_items si JOIN sales s ON s.id = si.sale_id
           WHERE s.sale_date > ? AND s.sale_date <= ? GROUP BY si.sku""", (since, today.isoformat()))
    return {r["sku"]: r["q"] / window for r in rows}


def reorder_report(conn: sqlite3.Connection, today: date) -> list[dict]:
    """补货建议（确定性公式）：

    日均销量 = 最近 120 天销量 / 120
    安全库存 = 产品设定值；没设时 = 14 天销量
    可用天数 = (现有库存 + 在途 - 安全库存) / 日均销量
    最晚下单日 = 今天 + 可用天数 - 采购交期
    另外检查：现有库存能不能撑到在途货到达（不能就是"到货前会断货"）。
    """
    rates = daily_rates(conn, today)
    out = []
    for s in stock_status(conn):
        rate = rates.get(s["sku"], 0.0)
        row = {**s, "daily_rate": round(rate, 2)}
        if rate <= 0:
            row.update(status="no_recent_sales", safety_used=s["safety_stock"], days_of_cover=None,
                       order_by=None, stockout_before_arrival=False)
            out.append(row)
            continue
        safety = s["safety_stock"] or round(rate * SAFETY_DAYS)
        days_cover = (s["on_hand"] + s["in_transit"] - safety) / rate
        order_by = today + timedelta(days=int(days_cover) - s["lead_time_days"])
        on_hand_days = s["on_hand"] / rate
        arrival_gap = (_d(s["next_arrival"]) - today).days if s["next_arrival"] else None
        stockout_before_arrival = arrival_gap is not None and on_hand_days < arrival_gap
        if s["on_hand"] == 0:
            status = "out_of_stock"
        elif order_by <= today:
            status = "order_now"
        elif order_by <= today + timedelta(days=SOON_DAYS):
            status = "order_soon"
        else:
            status = "ok"
        row.update(status=status, safety_used=safety, days_of_cover=round(days_cover, 1),
                   on_hand_days=round(on_hand_days, 1), order_by=order_by.isoformat(),
                   stockout_before_arrival=stockout_before_arrival)
        out.append(row)
    rank = {"out_of_stock": 0, "order_now": 1, "order_soon": 2, "ok": 3, "no_recent_sales": 4}
    return sorted(out, key=lambda r: (rank[r["status"]], r["order_by"] or "9999"))


def _customer_orders(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute(
        """SELECT c.code, s.sale_date FROM sales s JOIN customers c ON c.id = s.customer_id
           WHERE c.code <> ? ORDER BY s.sale_date""", (UNLABELED_CODE,))
    by: dict[str, list[str]] = {}
    for r in rows:
        by.setdefault(r["code"], []).append(r["sale_date"])
    return by


def top_products(conn: sqlite3.Connection, code: str, limit: int = 3) -> list[dict]:
    rows = conn.execute(
        """SELECT si.sku, p.name, SUM(si.qty) AS qty FROM sale_items si
           JOIN sales s ON s.id = si.sale_id JOIN customers c ON c.id = s.customer_id
           JOIN products p ON p.sku = si.sku
           WHERE c.code = ? GROUP BY si.sku ORDER BY qty DESC LIMIT ?""", (code, limit))
    return [dict(r) for r in rows]


def dormant_customers(conn: sqlite3.Connection, today: date) -> list[dict]:
    """沉睡客户（确定性规则）：至少 2 单，距上次下单的天数 > 平均下单间隔 × 2。按超期倍数排序。"""
    out = []
    for code, dates in _customer_orders(conn).items():
        ds = sorted({_d(x) for x in dates})
        if len(ds) < MIN_ORDERS_FOR_CYCLE:
            continue
        gap = mean((b - a).days for a, b in zip(ds, ds[1:]))
        silent = (today - ds[-1]).days
        if gap > 0 and silent > DORMANT_FACTOR * gap:
            out.append({"customer": code, "orders": len(ds), "avg_gap_days": round(gap, 1),
                        "days_since_last": silent, "overdue_ratio": round(silent / gap, 1),
                        "last_order": ds[-1].isoformat(), "usual_products": top_products(conn, code)})
    return sorted(out, key=lambda r: -r["overdue_ratio"])


def customer_history(conn: sqlite3.Connection, code: str, limit: int = 10) -> dict:
    cust = conn.execute("SELECT id, code, region, type, created_at FROM customers WHERE code = ?", (code,)).fetchone()
    if cust is None:
        return {"error": f"没有客户代号 {code}"}
    orders = conn.execute(
        """SELECT s.id, s.sale_date, t.total_qty, ROUND(t.total_usd, 2) AS total_usd
           FROM sales s JOIN v_sale_totals t ON t.sale_id = s.id
           WHERE s.customer_id = ? ORDER BY s.sale_date DESC LIMIT ?""", (cust["id"], limit))
    return {"customer": code, "region": cust["region"], "type": cust["type"],
            "recent_orders": [dict(r) for r in orders], "usual_products": top_products(conn, code, 5)}


def period_starts(today: date) -> dict[str, date]:
    """今年、本月、本周（周一开始）、今天的起始日期。"""
    return {"year": date(today.year, 1, 1), "month": date(today.year, today.month, 1),
            "week": today - timedelta(days=today.weekday()), "today": today}


def sales_stats(conn: sqlite3.Connection, today: date) -> list[dict]:
    """老板要的销售统计：每个时间段的订单数、件数、按原币种的收入（泰铢 / 美金 / 人民币 / USDT），
    以及折算成美元的合计；再按付款方式分开（转账 / 现金 / 未付款 / 历史订单未记录）。
    金额 = 数量 × 单价 × 折扣，只算已批准写入的订单。"""
    out = []
    for key, start in period_starts(today).items():
        args = (start.isoformat(), today.isoformat())
        n = conn.execute("SELECT COUNT(*) FROM sales WHERE sale_date >= ? AND sale_date <= ?", args).fetchone()[0]
        by_cur = {r["currency"]: r["amount"] for r in conn.execute(
            """SELECT si.currency, SUM(si.qty * si.unit_price * si.discount) AS amount
               FROM sale_items si JOIN sales s ON s.id = si.sale_id
               WHERE s.sale_date >= ? AND s.sale_date <= ? GROUP BY si.currency""", args)}
        units = conn.execute("""SELECT COALESCE(SUM(si.qty), 0) FROM sale_items si JOIN sales s ON s.id = si.sale_id
                                WHERE s.sale_date >= ? AND s.sale_date <= ?""", args).fetchone()[0]
        usd_total = conn.execute(
            """SELECT COALESCE(SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)), 0)
               FROM sale_items si JOIN sales s ON s.id = si.sale_id
               WHERE s.sale_date >= ? AND s.sale_date <= ?""", args).fetchone()[0]
        by_pay = {r["payment_method"]: {"orders": r["n"], "usd": r["usd"]} for r in conn.execute(
            """SELECT s.payment_method, COUNT(DISTINCT s.id) AS n,
                      SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)) AS usd
               FROM sales s JOIN sale_items si ON si.sale_id = s.id
               WHERE s.sale_date >= ? AND s.sale_date <= ? GROUP BY s.payment_method""", args)}
        out.append({"period": key, "from": start.isoformat(), "to": today.isoformat(), "orders": n, "units": units,
                    "thb": round(by_cur.get("THB", 0) or 0, 2), "usd": round((by_cur.get("USD", 0) or 0)
                                                                            + (by_cur.get("USDT", 0) or 0), 2),
                    "cny": round(by_cur.get("CNY", 0) or 0, 2), "total_usd": round(usd_total, 2),
                    "by_payment": by_pay})
    return out


def sales_summary(conn: sqlite3.Connection, today: date, days: int = 30) -> dict:
    since = (today - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """SELECT si.sku, p.name, SUM(si.qty) AS qty,
                  ROUND(SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)), 2) AS revenue_usd
           FROM sale_items si JOIN sales s ON s.id = si.sale_id JOIN products p ON p.sku = si.sku
           WHERE s.sale_date > ? AND s.sale_date <= ? GROUP BY si.sku ORDER BY revenue_usd DESC""",
        (since, today.isoformat()))
    items = [dict(r) for r in rows]
    n = conn.execute("SELECT COUNT(*) FROM sales WHERE sale_date > ? AND sale_date <= ?",
                     (since, today.isoformat())).fetchone()[0]
    return {"days": days, "orders": n, "revenue_usd": round(sum(i["revenue_usd"] for i in items), 2),
            "by_product": items}
