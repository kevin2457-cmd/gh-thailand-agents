"""重建本地数据库 data/app.db。

用法：
    python scripts/init_db.py                 # 默认用 data/sample/ 的模拟数据
    python scripts/init_db.py --source real   # 用 data/real/ 的真实数据（只在本机）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DB_PATH, DEFAULT_DATA_SOURCE, env_file_found  # noqa: E402
from backend.db import connect, init_db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["sample", "real"], default=DEFAULT_DATA_SOURCE)
    args = parser.parse_args()

    env = env_file_found()
    print(f".env: {env if env else '未找到（建库不需要 key，调用模型时才需要）'}")
    print(f"数据源: data/{args.source}/")

    counts = init_db(args.source)
    print(f"已重建 {DB_PATH}")
    for table, n in counts.items():
        print(f"  {table:<15} {n:>6}")

    conn = connect()
    negative = conn.execute("SELECT sku, on_hand FROM v_stock WHERE on_hand < 0").fetchall()
    conn.close()
    if negative:
        print("警告：以下 SKU 库存为负数，请检查数据：")
        for row in negative:
            print(f"  {row['sku']}: {row['on_hand']}")


if __name__ == "__main__":
    main()
