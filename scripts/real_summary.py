"""把真实数据的汇总数字（不含客户名、价格明细）存成 output/evidence/real_summary.json，供报告使用。

只在老板电脑上运行（需要 data/real.db 和 output/evidence/real_sales_import.json）。
"""
from __future__ import annotations

import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import EVIDENCE_DIR, REAL_DB_PATH  # noqa: E402


def main() -> None:
    imp = json.loads((EVIDENCE_DIR / "real_sales_import.json").read_text(encoding="utf-8"))
    ok = [r for r in imp["results"] if r["ok"]]
    kinds = collections.Counter()
    for r in ok:
        for w in r["result"]["checked"]["warnings"] + r["result"]["checked"]["blocking"]:
            if "算式不对" in w:
                kinds["line_math_mismatch"] += 1
            elif "总计不对" in w:
                kinds["total_mismatch"] += 1
            elif "低于底价" in w:
                kinds["below_floor_price"] += 1
            elif "有歧义" in w:
                kinds["ambiguous_product"] += 1
            elif "不在产品目录" in w:
                kinds["unknown_product"] += 1
            elif "没有单价" in w:
                kinds["missing_price"] += 1
            elif "请核对" in w:
                kinds["agent_inferred_sku"] += 1
    secs = [r["result"].get("seconds") for r in ok if r["result"].get("seconds")]
    conn = sqlite3.connect(REAL_DB_PATH)
    q = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
    summary = {
        "orders_imported": len(imp["results"]),
        "orders_parsed": len(ok),
        "orders_clean": sum(1 for r in ok if not r["result"]["checked"]["warnings"] and not r["result"]["checked"]["blocking"]),
        "orders_with_warnings": sum(1 for r in ok if r["result"]["checked"]["warnings"] and not r["result"]["checked"]["blocking"]),
        "orders_blocked": sum(1 for r in ok if r["result"]["checked"]["blocking"]),
        "finding_counts": dict(kinds),
        "import_cost_usd": imp["cost_usd"],
        "import_input_tokens": imp["input_tokens"],
        "import_cached_tokens": imp["cached_tokens"],
        "import_output_tokens": imp["output_tokens"],
        "seconds_per_order_median": sorted(secs)[len(secs) // 2] if secs else None,
        "products": q("SELECT COUNT(*) FROM products"),
        "containers": q("SELECT COUNT(*) FROM purchases"),
        "units_on_hand_at_stocktake": q("SELECT SUM(qty_change) FROM stock_moves WHERE reason = 'opening'"),
        "units_in_transit": q("SELECT COALESCE(SUM(in_transit), 0) FROM v_in_transit"),
        "products_sold_out_at_stocktake": q("SELECT COUNT(*) FROM v_stock WHERE on_hand = 0"),
        "approved_sales": q("SELECT COUNT(*) FROM sales"),
        "pending": q("SELECT COUNT(*) FROM pending_records WHERE status = 'pending'"),
    }
    conn.close()
    (EVIDENCE_DIR / "real_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
