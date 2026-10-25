"""作废一张已写入的销售单（例如员工试用时的测试单）。只有老板可以做，先备份数据库，写审计日志。

用法：python scripts/void_sale.py SO-000042 "原因" [--data real]
如果这张单动过库存（日期在盘点之后），对应的库存流水一起删除，库存自动恢复。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import db_path_for  # noqa: E402
from backend.db import connect  # noqa: E402
from backend.orders import audit  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sale_id")
    ap.add_argument("reason")
    ap.add_argument("--data", choices=["sample", "real"], default="sample")
    args = ap.parse_args()
    db = db_path_for(args.data)
    backup = db.with_name(f"{db.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}.db")
    shutil.copy2(db, backup)
    conn = connect(db)
    sale = conn.execute("SELECT * FROM sales WHERE id = ?", (args.sale_id,)).fetchone()
    if sale is None:
        raise SystemExit(f"没有销售单 {args.sale_id}")
    items = [dict(r) for r in conn.execute("SELECT sku, qty FROM sale_items WHERE sale_id = ?", (args.sale_id,))]
    moves = conn.execute("DELETE FROM stock_moves WHERE ref_id = ? AND reason = 'sale'", (args.sale_id,)).rowcount
    conn.execute("DELETE FROM sale_items WHERE sale_id = ?", (args.sale_id,))
    conn.execute("DELETE FROM sales WHERE id = ?", (args.sale_id,))
    conn.execute("UPDATE pending_records SET status = 'rejected', review_note = ? WHERE result_ref = ?",
                 (f"作废：{args.reason}", args.sale_id))
    audit(conn, "U01", "owner", "void", "sales", args.sale_id,
          {"reason": args.reason, "date": sale["sale_date"], "items": items, "stock_moves_removed": moves})
    conn.commit()
    conn.close()
    print(f"已作废 {args.sale_id}（{sale['sale_date']}，{len(items)} 行，删除库存流水 {moves} 条）；备份 {backup.name}")


if __name__ == "__main__":
    main()
