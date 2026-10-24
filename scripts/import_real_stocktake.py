"""把最后一次盘点（Word）转成 data/real/opening_stock.csv，作为库存起点。

输入：data/real/raw/stocktake/*.docx（gitignored）。格式是一行一个产品，例如 "Bio root 6 gal =24"。
规则（老板确认）：
  - 分隔线 ——— 只是分组，全部是同一个仓库
  - 同名产品合并数量（同样名字的都是同规格）
  - 产品目录里有、盘点里没出现的产品 = 已经卖完，库存 0
  - "General Hydro" 段下的 Bloom / Micro 是 FloraPro 25lb；"ATHENA" 段下的是 Athena
同时补齐 real 数据集需要的其他文件（users；customers/sales/sale_items 先建空表头，等销售导入）。

用法：python scripts/import_real_stocktake.py   （先运行 import_real_purchases.py 生成 products.csv）
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.catalog import lookup, norm  # noqa: E402
from backend.config import REAL_DIR  # noqa: E402

RAW = REAL_DIR / "raw" / "stocktake"
YEAR = 2026

# 只有在某一段下面才有意义的短名字
SECTION_ALIASES = {
    ("generalhydro", "bloom"): "FP-BLOOM-25LB",
    ("generalhydro", "micro"): "FP-CAMICRO-25LB",
    ("generalhydro", "grow"): "FP-GROW-25LB",
    ("generalhydro", "latebloom"): "FP-LATEBLOOM-25LB",
    ("athena", "core"): "ATH-PRO-CORE-25LB",
    ("athena", "bloom"): "ATH-PRO-BLOOM-25LB",
    ("athena", "grow"): "ATH-PRO-GROW-25LB",
    ("athena", "cleanse"): "ATH-CLEANSE-5G",
    ("athena", "fade"): "ATH-FADE-5G",
    ("athena", "balance"): "ATH-BALANCE-25LB",
}

LINE = re.compile(r"^(?P<name>.+?)\s*=?\s*(?P<qty>\d+)\s*$")
AS_OF = re.compile(r"截至\s*(\d{1,2})\s*/\s*(\d{1,2})")


def main() -> None:
    files = sorted(RAW.glob("*.docx"))
    if len(files) != 1:
        raise SystemExit(f"{RAW} 里应该正好有 1 个盘点 .docx，现在有 {len(files)} 个")
    lines = [p.text.strip() for p in docx.Document(files[0]).paragraphs if p.text.strip()]

    as_of, section, counts, sources = None, "", {}, {}
    for text in lines:
        m = AS_OF.search(text)
        if m:
            as_of = f"{YEAR}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
            continue
        if set(text) <= set("—-_ "):
            continue  # 分隔线
        m = LINE.match(text)
        if not m:
            section = norm(text)  # 没有数字的行是分段标题，例如 "General Hydro"、"ATHENA"
            continue
        name, qty = m.group("name").strip(" =:："), int(m.group("qty"))
        sku = SECTION_ALIASES.get((section, norm(name))) or lookup(name)
        if sku is None:
            raise SystemExit(f"盘点里的产品名 {text!r} 不认识：请加进 backend/catalog.py 的别名，并和老板确认。")
        counts[sku] = counts.get(sku, 0) + qty
        sources.setdefault(sku, []).append(text)
    if as_of is None:
        raise SystemExit("没找到盘点日期（例如 '截至10/24'）")

    with (REAL_DIR / "products.csv").open(encoding="utf-8") as f:
        catalog_skus = [r["sku"] for r in csv.DictReader(f)]
    unknown = set(counts) - set(catalog_skus)
    if unknown:
        raise SystemExit(f"盘点里的 {sorted(unknown)} 不在 products.csv 里：先运行 import_real_purchases.py")

    with (REAL_DIR / "opening_stock.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sku", "as_of_date", "qty"])
        for sku in catalog_skus:
            w.writerow([sku, as_of, counts.get(sku, 0)])

    # real 数据集需要的其他文件
    def ensure(name: str, header: list[str], rows: list[tuple] = ()) -> None:
        path = REAL_DIR / f"{name}.csv"
        if not path.exists():
            with path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows)

    ensure("users", ["id", "name", "role"], [("U01", "Kevin (owner)", "owner"), ("U02", "Staff", "staff")])
    ensure("customers", ["id", "code", "name", "phone", "address", "wechat_alias", "region", "type", "created_at"])
    ensure("sales", ["id", "sale_date", "customer_id", "source", "note"])
    ensure("sale_items", ["sale_id", "sku", "qty", "unit_price"])

    print(f"盘点日期 {as_of}：{len(lines)} 行 → {len(counts)} 个产品有库存，"
          f"{len(catalog_skus) - len(counts)} 个产品库存为 0（已卖完）")
    for sku in sorted(counts, key=lambda s: -counts[s]):
        merged = f"  ← 合并 {len(sources[sku])} 行" if len(sources[sku]) > 1 else ""
        print(f"  {sku:<26} {counts[sku]:>5}{merged}")


if __name__ == "__main__":
    main()
