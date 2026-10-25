"""客户档案：编辑、新建、购买习惯、把未标注客户的订单归档。"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import customers as cu  # noqa: E402
from backend.db import connect, init_db  # noqa: E402
from backend.orders import OrderDraft, OrderLineDraft, approve, ensure_customer, submit, validate  # noqa: E402

TODAY = date(2026, 10, 23)


@pytest.fixture()
def conn(tmp_path):
    init_db("sample", db_path=tmp_path / "t.db")
    c = connect(tmp_path / "t.db")
    yield c
    c.close()


def test_edit_customer_and_audit_has_no_private_values(conn):
    cu.save_customer(conn, "CUST-003", {"name": "New Name", "phone": "0899999999", "address": "1 Road",
                                        "notes": "likes Athena, pays on time"}, "U01")
    c = cu.get_customer(conn, "CUST-003")
    assert (c["name"], c["phone"], c["notes"]) == ("New Name", "0899999999", "likes Athena, pays on time")
    detail = conn.execute("SELECT detail_json FROM audit_log WHERE action = 'customer_edit'").fetchone()[0]
    assert "0899999999" not in detail and "phone" in json.loads(detail)["fields"]


def test_create_customer_and_reject_duplicates(conn):
    code = cu.save_customer(conn, None, {"name": "Brand New Shop", "region": "Phuket", "type": "farm"}, "U02")
    assert cu.get_customer(conn, code)["region"] == "Phuket"
    with pytest.raises(ValueError):
        cu.save_customer(conn, None, {"name": "Brand New Shop"}, "U01")
    with pytest.raises(ValueError):
        cu.save_customer(conn, code, {"name": "  "}, "U01")


def test_profile_shows_buying_habits(conn):
    p = cu.profile(conn, "CUST-006", TODAY)
    assert p["orders"] >= 2 and p["avg_gap_days"] and p["usual_products"]
    assert p["days_since_last"] > 60 and p["total_usd"] > 0


def test_assign_unlabeled_orders(conn):
    ensure_customer(conn, "UNLABELED")
    d = OrderDraft(order_date="2026-06-25", lines=[OrderLineDraft(product_text="B52", qty=1, unit_price=600,
                                                                   currency="USD")])
    pid = submit(conn, customer_code="UNLABELED", checked=validate(conn, d, "", TODAY, customer_code="UNLABELED"),
                 source_type="report", source_text="", submitted_by="U01")
    sale = approve(conn, pid, "U01")
    assert [s["id"] for s in cu.unlabeled_sales(conn)] == [sale]
    before = cu.profile(conn, "CUST-002", TODAY)["orders"]
    assert cu.assign_sales(conn, [sale], "CUST-002", "U01") == 1
    assert cu.unlabeled_sales(conn) == []
    assert cu.profile(conn, "CUST-002", TODAY)["orders"] == before + 1
    with pytest.raises(ValueError):
        cu.assign_sales(conn, [sale], "UNLABELED", "U01")


def test_spend_ranking_matches_profiles(conn):
    sp = cu.spend_ranking(conn)
    totals = [r["total_usd"] for r in sp["rows"]]
    assert totals == sorted(totals, reverse=True) and all(r["code"] != "UNLABELED" for r in sp["rows"])
    top = sp["rows"][0]
    assert round(top["total_usd"], 2) == cu.profile(conn, top["code"], TODAY)["total_usd"]
    assert abs(sum(r["share"] for r in sp["rows"]) - 100) < 1
