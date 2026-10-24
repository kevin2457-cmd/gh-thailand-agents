"""骨架冒烟测试：模拟数据能建库，数据符合演示场景，.env 读取顺序正确。

运行：python -m pytest -q
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import config  # noqa: E402
from backend.db import connect, init_db  # noqa: E402

TODAY = date(2026, 10, 23)


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    db = tmp_path_factory.mktemp("db") / "test.db"
    init_db("sample", db_path=db)
    c = connect(db)
    yield c
    c.close()


def test_env_lookup_order():
    assert config.ENV_FILES == [config.ROOT_DIR / ".env", config.ROOT_DIR.parent / ".env"]
    assert config.MODEL_NAME == "gpt-6-luna"


def test_all_tables_loaded(conn):
    for table in ["users", "suppliers", "products", "customers", "sales", "sale_items",
                  "purchases", "purchase_items", "stock_moves"]:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 0, table


def test_no_negative_stock(conn):
    assert conn.execute("SELECT COUNT(*) FROM v_stock WHERE on_hand < 0").fetchone()[0] == 0


def test_stock_moves_match_sales_and_receipts(conn):
    sold = conn.execute("SELECT SUM(qty) FROM sale_items").fetchone()[0]
    moved_out = conn.execute("SELECT -SUM(qty_change) FROM stock_moves WHERE reason = 'sale'").fetchone()[0]
    assert sold == moved_out


def test_stocktake_is_starting_point(tmp_path):
    """盘点之前的销售和到货不能再扣/加一次库存（真实数据就是这种情况）。"""
    import csv
    import shutil

    from backend import db as dbmod

    src = tmp_path / "data"
    shutil.copytree(config.SAMPLE_DIR, src)
    rows = list(csv.DictReader((src / "opening_stock.csv").open(encoding="utf-8")))
    with (src / "opening_stock.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sku", "as_of_date", "qty"])
        for r in rows:
            w.writerow([r["sku"], "2099-01-01", 7])  # 盘点日期晚于所有交易

    orig = dbmod.data_dir_for
    dbmod.data_dir_for = lambda source: src
    try:
        dbmod.init_db("sample", db_path=tmp_path / "t.db")
    finally:
        dbmod.data_dir_for = orig
    c = connect(tmp_path / "t.db")
    on_hand = {r["sku"]: r["on_hand"] for r in c.execute("SELECT sku, on_hand FROM v_stock")}
    c.close()
    assert set(on_hand.values()) == {7}


def test_demo_scenarios_present(conn):
    # 有 SKU 处于或低于安全库存
    low = conn.execute("SELECT COUNT(*) FROM v_stock WHERE on_hand <= safety_stock").fetchone()[0]
    assert low >= 1
    # 有在途采购单
    assert conn.execute("SELECT COUNT(*) FROM v_in_transit").fetchone()[0] >= 1
    # 有客户超过 60 天没有下单（沉睡客户的候选）
    rows = conn.execute("SELECT customer_id, MAX(sale_date) AS last FROM sales GROUP BY customer_id").fetchall()
    silent = [r for r in rows if (TODAY - date.fromisoformat(r["last"])).days > 60]
    assert len(silent) >= 3


def test_private_fields_separate_from_code(conn):
    row = conn.execute("SELECT code, name, phone FROM customers LIMIT 1").fetchone()
    assert row["code"].startswith("CUST-")
    assert row["code"] not in row["name"]
