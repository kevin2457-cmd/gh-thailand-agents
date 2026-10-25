"""客户档案：编辑 / 新建客户、购买习惯、把"未标注客户"的历史订单归到某个客户。

名字、电话、地址、备注只存在本地数据库；agent 永远只看到客户代号（CUST-007）。
审计日志只记录"改了哪些字段"，不记录字段内容（隐私）。
"""
from __future__ import annotations

import sqlite3
from datetime import date
from statistics import mean

from backend.analytics import top_products
from backend.config import UNLABELED_CODE
from backend.orders import audit, user_role

EDITABLE = ("name", "wechat_alias", "phone", "address", "region", "type", "notes")
TYPES = ("grow_shop", "farm", "reseller", "retail")


def get_customer(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM customers WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def save_customer(conn: sqlite3.Connection, code: str | None, fields: dict, user_id: str) -> str:
    """code 为 None 时新建客户，否则更新。返回客户代号。"""
    role = user_role(conn, user_id)
    data = {k: (fields.get(k) or "").strip() for k in EDITABLE if k in fields}
    if "name" in data and not data["name"]:
        raise ValueError("客户名字不能为空")
    if data.get("type") and data["type"] not in TYPES:
        raise ValueError(f"未知客户类型 {data['type']}")
    if code is None:
        if not data.get("name"):
            raise ValueError("客户名字不能为空")
        if conn.execute("SELECT 1 FROM customers WHERE name = ?", (data["name"],)).fetchone():
            raise ValueError("已经有同名客户")
        n = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] + 1
        while conn.execute("SELECT 1 FROM customers WHERE id = ? OR code = ?", (f"C{n:03d}", f"CUST-{n:03d}")).fetchone():
            n += 1
        code = f"CUST-{n:03d}"
        conn.execute("INSERT INTO customers (id, code, name, phone, address, wechat_alias, region, type, created_at, notes) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (f"C{n:03d}", code, data["name"], data.get("phone", ""), data.get("address", ""),
                      data.get("wechat_alias") or data["name"], data.get("region") or "unknown",
                      data.get("type") or "grow_shop", date.today().isoformat(), data.get("notes", "")))
        audit(conn, user_id, role, "customer_create", "customers", code, {"fields": sorted(k for k, v in data.items() if v)})
    else:
        if code == UNLABELED_CODE:
            raise ValueError("「未标注客户」不能编辑")
        old = get_customer(conn, code)
        if old is None:
            raise ValueError(f"客户 {code} 不存在")
        changed = {k: v for k, v in data.items() if (old.get(k) or "") != v}
        if changed:
            sets = ", ".join(f"{k} = ?" for k in changed)
            conn.execute(f"UPDATE customers SET {sets} WHERE code = ?", (*changed.values(), code))
            audit(conn, user_id, role, "customer_edit", "customers", code, {"fields": sorted(changed)})
    conn.commit()
    return code


def profile(conn: sqlite3.Connection, code: str, today: date) -> dict:
    """购买习惯（全部由代码计算）：订单数、首次/最近下单、平均间隔、多久没下单、总消费、常买产品、最近订单。"""
    cust = get_customer(conn, code)
    if cust is None:
        return {}
    orders = [dict(r) for r in conn.execute(
        """SELECT s.id, s.sale_date, s.payment_method, SUM(si.qty) AS units,
                  SUM(CASE WHEN si.currency = 'THB' THEN si.qty * si.unit_price * si.discount ELSE 0 END) AS thb,
                  SUM(CASE WHEN si.currency IN ('USD', 'USDT') THEN si.qty * si.unit_price * si.discount ELSE 0 END) AS usd,
                  SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)) AS total_usd
           FROM sales s JOIN sale_items si ON si.sale_id = s.id
           WHERE s.customer_id = ? GROUP BY s.id ORDER BY s.sale_date DESC""", (cust["id"],))]
    dates = sorted({date.fromisoformat(o["sale_date"]) for o in orders})
    gap = round(mean((b - a).days for a, b in zip(dates, dates[1:])), 1) if len(dates) >= 2 else None
    return {
        "customer": cust, "orders": len(orders), "first": dates[0].isoformat() if dates else None,
        "last": dates[-1].isoformat() if dates else None, "avg_gap_days": gap,
        "days_since_last": (today - dates[-1]).days if dates else None,
        "thb": round(sum(o["thb"] or 0 for o in orders), 2), "usd": round(sum(o["usd"] or 0 for o in orders), 2),
        "total_usd": round(sum(o["total_usd"] or 0 for o in orders), 2),
        "usual_products": top_products(conn, code, 6), "recent": orders[:10],
    }


def unlabeled_sales(conn: sqlite3.Connection) -> list[dict]:
    """还没有客户的历史订单（导入时报告里没写客户），方便老板逐单归档。"""
    rows = conn.execute(
        """SELECT s.id, s.sale_date, GROUP_CONCAT(p.name || ' ×' || si.qty, ', ') AS items,
                  SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)) AS total_usd
           FROM sales s JOIN customers c ON c.id = s.customer_id
           JOIN sale_items si ON si.sale_id = s.id JOIN products p ON p.sku = si.sku
           WHERE c.code = ? GROUP BY s.id ORDER BY s.sale_date""", (UNLABELED_CODE,))
    return [dict(r) for r in rows]


def assign_sales(conn: sqlite3.Connection, sale_ids: list[str], code: str, user_id: str) -> int:
    """把订单归到某个客户名下（只能改"未标注客户"的订单，已经有客户的不会被误改）。"""
    role = user_role(conn, user_id)
    cust = get_customer(conn, code)
    if cust is None or code == UNLABELED_CODE:
        raise ValueError("请选择一个真实客户")
    unl = conn.execute("SELECT id FROM customers WHERE code = ?", (UNLABELED_CODE,)).fetchone()
    if unl is None or not sale_ids:
        return 0
    n = 0
    for sid in sale_ids:
        n += conn.execute("UPDATE sales SET customer_id = ? WHERE id = ? AND customer_id = ?",
                          (cust["id"], sid, unl["id"])).rowcount
    audit(conn, user_id, role, "assign_sales", "customers", code, {"sales": list(sale_ids), "updated": n})
    conn.commit()
    return n


def spend_ranking(conn: sqlite3.Connection) -> dict:
    """每位客户的累计消费（按原币种 + 折合美元），从高到低排；另给出全部客户合计和"未标注客户"的金额。"""
    rows = [dict(r) for r in conn.execute(
        """SELECT c.code, c.region, COUNT(DISTINCT s.id) AS orders, MAX(s.sale_date) AS last,
                  COALESCE(SUM(CASE WHEN si.currency = 'THB' THEN si.qty * si.unit_price * si.discount END), 0) AS thb,
                  COALESCE(SUM(CASE WHEN si.currency IN ('USD', 'USDT') THEN si.qty * si.unit_price * si.discount END), 0) AS usd,
                  COALESCE(SUM(si.qty * COALESCE(si.unit_price_usd, si.unit_price)), 0) AS total_usd
           FROM customers c LEFT JOIN sales s ON s.customer_id = c.id LEFT JOIN sale_items si ON si.sale_id = s.id
           GROUP BY c.id""")]
    unl = next((r for r in rows if r["code"] == UNLABELED_CODE), None)
    rows = sorted((r for r in rows if r["code"] != UNLABELED_CODE), key=lambda r: (-r["total_usd"], r["code"]))
    total = sum(r["total_usd"] for r in rows)
    for r in rows:
        r["share"] = round(100 * r["total_usd"] / total, 1) if total else 0.0
        r["avg_order_usd"] = round(r["total_usd"] / r["orders"], 2) if r["orders"] else 0.0
    return {"rows": rows, "total_usd": round(total, 2), "thb": round(sum(r["thb"] for r in rows), 2),
            "usd": round(sum(r["usd"] for r in rows), 2),
            "unlabeled_usd": round(unl["total_usd"], 2) if unl else 0.0, "unlabeled_orders": unl["orders"] if unl else 0}
