"""SQLite 连接和建库。

init_db(source) 会删除旧数据库，按 schema.sql 建表，从 data/<source>/ 的 CSV 导入数据，
再根据期初库存、销售、到货生成库存流水（stock_moves）。
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from backend.config import SCHEMA_PATH, active_db, data_dir_for, db_path_for

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


# 后来加的列：已经建好的数据库（例如老板电脑上的 data/real.db）打开时自动补上，不用重建
MIGRATIONS = [
    ("pending_records", "payment_method", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("pending_records", "payment_file", "TEXT"),
    ("sales", "payment_method", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("sales", "payment_file", "TEXT"),
    ("customers", "notes", "TEXT NOT NULL DEFAULT ''"),  # 客户档案备注（购买习惯、偏好……），只存在本地
]
_migrated: set[str] = set()


def migrate(conn: sqlite3.Connection) -> None:
    for table, col, ddl in MIGRATIONS:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if cols and col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    conn.commit()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or active_db()
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if str(path) not in _migrated and Path(path).exists():
        migrate(conn)
        _migrated.add(str(path))
    return conn


# 这些列的空字符串存成 NULL（例如在途采购单还没有 received_date）；其他列保留空字符串，例如品牌未知
NULL_IF_EMPTY = {"received_date"}


def _read_csv(path: Path) -> list[dict[str, str | None]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (None if v == "" and k in NULL_IF_EMPTY else v) for k, v in row.items()}
                for row in csv.DictReader(f)]


def _insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    conn.executemany(sql, [[r[c] for c in cols] for r in rows])


def _build_stock_moves(conn: sqlite3.Connection, opening: list[dict]) -> None:
    """期初库存（或盘点）是起点：只有起点之后的销售和到货才算进库存，之前的已经包含在盘点数里。"""
    conn.execute("CREATE TEMP TABLE opening (sku TEXT PRIMARY KEY, as_of_date TEXT NOT NULL)")
    conn.executemany("INSERT INTO opening VALUES (?, ?)", [(r["sku"], r["as_of_date"]) for r in opening])
    conn.executemany(
        "INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id) VALUES (?, ?, ?, 'opening', NULL)",
        [(r["sku"], r["as_of_date"], int(r["qty"])) for r in opening if int(r["qty"]) != 0],
    )
    after_opening = "{date} > COALESCE((SELECT as_of_date FROM opening o WHERE o.sku = {sku}), '0000-00-00')"
    conn.execute(
        f"""INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id)
           SELECT si.sku, s.sale_date, -si.qty, 'sale', s.id
           FROM sale_items si JOIN sales s ON s.id = si.sale_id
           WHERE {after_opening.format(date='s.sale_date', sku='si.sku')}"""
    )
    conn.execute(
        f"""INSERT INTO stock_moves (sku, move_date, qty_change, reason, ref_id)
           SELECT pi.sku, pu.received_date, pi.qty, 'purchase_receipt', pu.id
           FROM purchase_items pi JOIN purchases pu ON pu.id = pi.purchase_id
           WHERE pu.status = 'received' AND {after_opening.format(date='pu.received_date', sku='pi.sku')}"""
    )
    conn.execute("DROP TABLE opening")


def init_db(source: str = "sample", db_path: Path | None = None) -> dict[str, int]:
    """重建数据库并导入数据，返回每张表的行数。"""
    src = data_dir_for(source)
    db_path = db_path or db_path_for(source)
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
