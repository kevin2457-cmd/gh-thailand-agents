"""老板 10/24 晚上提的功能：付款方式和凭证、现金要老板确认、销售统计、库存搜索。"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import analytics  # noqa: E402
from backend.db import connect, init_db  # noqa: E402
from backend.orders import (CASH_BLOCK, OrderDraft, OrderLineDraft, approve, confirm_cash, submit,  # noqa: E402
                            validate)

TODAY = date(2026, 10, 23)


@pytest.fixture()
def conn(tmp_path):
    init_db("sample", db_path=tmp_path / "t.db")
    c = connect(tmp_path / "t.db")
    yield c
    c.close()


def order(conn, qty=1, price=600, cur="USD", day="2026-10-22", **pay):
    d = OrderDraft(order_date=day, lines=[OrderLineDraft(product_text="B52", qty=qty, unit_price=price, currency=cur)])
    chk = validate(conn, d, "", TODAY, customer_code="CUST-002")
    return submit(conn, customer_code="CUST-002", checked=chk, source_type="wechat", source_text="",
                  submitted_by="U02", **pay)


def test_cash_needs_owner_confirmation(conn):
    pid = order(conn, payment_method="cash")
    with pytest.raises(ValueError):
        approve(conn, pid, "U01")
    with pytest.raises(PermissionError):
        confirm_cash(conn, pid, "U02")  # 员工不能确认现金
    confirm_cash(conn, pid, "U01")
    sale = approve(conn, pid, "U01")
    assert conn.execute("SELECT payment_method FROM sales WHERE id = ?", (sale,)).fetchone()[0] == "cash"
    assert "cash_confirmed" in [r[0] for r in conn.execute("SELECT action FROM audit_log")]


def test_transfer_without_screenshot_warns(conn):
    import json
    pid = order(conn, payment_method="transfer")
    warns = json.loads(conn.execute("SELECT warnings FROM pending_records WHERE id = ?", (pid,)).fetchone()[0])
    assert "转账但没有上传付款截图" in warns
    pid2 = order(conn, qty=2, payment_method="transfer", payment_file="data/payments/x.jpg")
    row = conn.execute("SELECT warnings, payment_file FROM pending_records WHERE id = ?", (pid2,)).fetchone()
    assert "转账但没有上传付款截图" not in json.loads(row[0]) and row[1] == "data/payments/x.jpg"
    assert CASH_BLOCK not in json.loads(row[0])


def test_sales_stats_by_period_and_currency(conn):
    before = {p["period"]: p for p in analytics.sales_stats(conn, TODAY)}
    approve(conn, order(conn, qty=2, price=8500, cur="THB", day="2026-10-23", payment_method="unpaid"), "U01")
    after = {p["period"]: p for p in analytics.sales_stats(conn, TODAY)}
    assert after["today"]["orders"] == before["today"]["orders"] + 1
    assert after["today"]["thb"] == pytest.approx(before["today"]["thb"] + 17000)
    assert after["year"]["orders"] == before["year"]["orders"] + 1
    assert after["today"]["by_payment"]["unpaid"]["orders"] == 1
    assert set(after) == {"year", "month", "week", "today"}


def test_inventory_search_matches_nicknames():
    import app
    assert "GROTEK-MONSTER-BLOOM" in app.match_products("紫粉")
    assert {"GH-FLORALICIOUS-PLUS-6GAL", "GH-FLORALICIOUS-PLUS-1GAL"} <= app.match_products("香味")
    assert "AN-BIG-BUD" in app.match_products("big bud")
    assert app.match_products("") is None
