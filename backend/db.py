"""SQLite 连接和建库。

init_db(source) 会删除旧数据库，按 schema.sql 建表，从 data/<source>/ 的 CSV 导入数据，
再根据期初库存、销售、到货生成库存流水（stock_moves）。
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from backend.config import DB_PATH, SCHEMA_PATH, data_dir_for

# 导入顺序（按外键依赖排列）。opening_stock.csv 不是一张表，单独处理。
TABLES = [
    "users",
    "suppliers",
    "products",
    "customers",
    "sales",
    "sale_items",
    "purchases",
    "purchase_items",
]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _read_csv(path: Path) -> list[dict[str, str | None]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        # 空字符串存成 NULL（例如在途采购单的 received_date）
        return [{k: (v if v != "" else None) for k, v in row.items()} for row in csv.DictReader(f)]


def _insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    conn.executemany(sql, [[r[c] for c in cols] for r in rows])


def _build_stock_moves(conn: sqlite3.Connection, opening: list[dict]) -> None:
    conn.executemany(
        "INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id) VALUES (?, ?, ?, 'opening', NULL)",
        [(r["sku"], r["as_of_date"], int(r["qty"])) for r in opening if int(r["qty"]) != 0],
    )
    conn.execute(
        """INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id)
           SELECT si.sku, s.sale_date, -si.qty, 'sale', s.id
           FROM sale_items si JOIN sales s ON s.id = si.sale_id"""
    )
    conn.execute(
        """INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id)
           SELECT pi.sku, pu.received_date, pi.qty, 'purchase_receipt', pu.id
           FROM purchase_items pi JOIN purchases pu ON pu.id = pi.purchase_id
           WHERE pu.status = 'received'"""
    )


def init_db(source: str = "sample", db_path: Path = DB_PATH) -> dict[str, int]:
    """重建数据库并导入数据，返回每张表的行数。"""
    src = data_dir_for(source)
    missing = [f"{t}.csv" for t in TABLES + ["opening_stock"] if not (src / f"{t}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"{src} 缺少文件：{', '.join(missing)}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table in TABLES:
            _insert_rows(conn, table, _read_csv(src / f"{table}.csv"))
        _build_stock_moves(conn, _read_csv(src / "opening_stock.csv"))
        conn.commit()
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES + ["stock_moves"]}
    finally:
        conn.close()
    return counts
