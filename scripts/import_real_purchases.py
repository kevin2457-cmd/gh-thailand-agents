"""把真实的采购（货柜）Excel 转成 data/real/ 下的 CSV。

输入：data/real/raw/excel/ 下每个货柜的核算表（gitignored，只在本机）
输出：data/real/suppliers.csv, products.csv, purchases.csv, purchase_items.csv

只取数量、拿货价、运费、建议零售价、建议销售底价。股东分成等内部数字不导入。
所有产品写法（英文变体、中文俗称）都映射到一个标准 SKU，统计时只用标准 SKU。
遇到映射表里没有的产品名会直接报错，不会猜。

用法：python scripts/import_real_purchases.py
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.catalog import CATALOG, EARLY_STOCK_SKUS, lookup, norm  # noqa: E402
from backend.config import REAL_DIR  # noqa: E402

RAW = REAL_DIR / "raw" / "excel"
LEAD_TIME_DAYS = 60  # 老板确认：大约每 2 个月发一柜、到一柜
SUPPLIER = ("S01", "US brands via Los Angeles container", "USA", LEAD_TIME_DAYS)

# 每个货柜：读哪个文件、日期。到货日期按文件夹名；下单日期 = 到货 - 60 天（老板确认按 2 个月算）。
# 第一柜：数量按"洛杉矶 货品清单"的总计列（老板确认按多的结算），价格按"泰国 药水核算"。
# 2025 年 2 月到 11 月之间的货柜文件已经找不到。当前库存以最后一次盘点为准，所以这段缺口不影响库存，
# 只影响那段时间的采购统计（报告里要说明）。
CONTAINERS = [
    {"id": "PO-R01", "label": "第一柜", "qty_file": "第一柜/洛杉矶 货品清单.xlsx", "qty_col": "总计",
     "price_file": "第一柜/泰国 药水核算.xlsx", "ordered": date(2024, 12, 16), "arrived": True},
    {"id": "PO-R02", "label": "11-4-2025 柜子", "file": "26-01-01/11-4-2025柜子.xlsx",
     "ordered": date(2025, 11, 4), "arrived": True},
    {"id": "PO-R03", "label": "2 月货柜", "file": "26-02-01/2月货柜.xlsx",
     "ordered": date(2026, 2, 1) - timedelta(days=LEAD_TIME_DAYS), "arrived": True},
    {"id": "PO-R04", "label": "4 月货柜（内部）", "file": "26-04-01/26年4月货柜 内部.xlsx",
     "ordered": date(2026, 4, 1) - timedelta(days=LEAD_TIME_DAYS), "arrived": True},
    {"id": "PO-R05", "label": "10 月货柜（在途）", "file": "26年10月货柜 内部(1).xlsx",
     "ordered": date(2026, 10, 15), "arrived": False},
]


# 采购 Excel 里不带规格、但老板确认 Excel 都是最大规格的产品
EXCEL_NAME_OVERRIDES = {norm(n): "GH-FLORALICIOUS-PLUS-6GAL" for n in ("Floralicious", "香味")}


def to_sku(raw_name: str, where: str) -> str:
    sku = EXCEL_NAME_OVERRIDES.get(norm(raw_name)) or lookup(raw_name)
    if sku is None:
        raise SystemExit(f"未知产品名 {raw_name!r}（{where}）：请先加进 backend/catalog.py 的别名里，并和老板确认。")
    return sku


def read_table(path: Path) -> tuple[list[dict], dict]:
    """读第一个工作表：找到含 Product name 的表头行，返回产品行和合计行里的数字。"""
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(rows) if "Product name" in r)
    col: dict[str, int] = {}
    for j, v in enumerate(rows[h]):
        if v is not None and str(v).strip() not in col:  # 有两列 Product name 时取第一列
            col[str(v).strip()] = j
    name_j = col["Product name"]
    items, totals = [], {}
    for r in rows[h + 1:]:
        name = r[name_j]
        if name is None or str(name).startswith(("总计", "总运费", "每桶")):
            # 合计行：把"标签 | 数字"成对记下，用来核对
            for j in range(len(r) - 1):
                if isinstance(r[j], str) and isinstance(r[j + 1], (int, float)):
                    totals[r[j].strip()] = r[j + 1]
            continue
        items.append({k: r[j] for k, j in col.items()})
    return items, totals


def num(v) -> float:
    return float(v) if isinstance(v, (int, float)) else 0.0


def main() -> None:
    purchases, purchase_items, checks = [], [], []
    latest_price: dict[str, dict] = {}  # sku -> 最近一柜的价格（CONTAINERS 按时间顺序）

    for c in CONTAINERS:
        if "file" in c:
            path = RAW / c["file"]
            rows, totals = read_table(path)
            lines = [(to_sku(r["Product name"], c["file"]), num(r["当量"]), r) for r in rows]
        else:
            qty_rows, _ = read_table(RAW / c["qty_file"])
            price_rows, totals = read_table(RAW / c["price_file"])
            prices = {to_sku(r["Product name"], c["price_file"]): r for r in price_rows}
            lines = []
            for r in qty_rows:
                sku = to_sku(r["Product name"], c["qty_file"])
                pr = prices.get(sku)
                if pr is None:  # 只在洛杉矶清单里出现的产品：拿货价 = 批发价 + 10（和其他产品一致）
                    pr = {"拿货价": num(r["批发价"]) + 10, "加运费": num(r["批发价"]) + 21,
                          "建议零售价": None, "建议销售底价": None}
                    checks.append(f"{sku}：第一柜核算表里没有，拿货价按 洛杉矶批发价 + 10 估算")
                lines.append((sku, num(r[c["qty_col"]]), pr))

        expected = c["ordered"] + timedelta(days=LEAD_TIME_DAYS)
        purchases.append((c["id"], SUPPLIER[0], c["ordered"].isoformat(), expected.isoformat(),
                          expected.isoformat() if c["arrived"] else "", "received" if c["arrived"] else "ordered",
                          c["label"]))
        merged: dict[str, list] = {}
        for sku, qty, r in lines:
            cost, landed = num(r["拿货价"]), num(r["加运费"])
            latest_price[sku] = {"cost": cost, "freight": round(landed - cost, 2),
                                 "price": r.get("建议零售价"), "floor": r.get("建议销售底价")}
            if qty > 0:
                if sku in merged:
                    checks.append(f"{c['label']}：{sku} 出现两次，数量已合并")
                    merged[sku][0] += qty
                else:
                    merged[sku] = [qty, cost, round(landed - cost, 2)]
        for sku, (qty, cost, freight) in merged.items():
            purchase_items.append((c["id"], sku, int(qty), cost, freight))

        # 和 Excel 自己的合计核对
        total_qty = sum(v[0] for v in merged.values())
        total_cost = sum(v[0] * v[1] for v in merged.values())
        xl_qty, xl_cost = totals.get("总计（桶）"), totals.get("货物总成本")
        ok = (xl_qty is None or abs(total_qty - xl_qty) < 0.5) and (xl_cost is None or abs(total_cost - xl_cost) < 1)
        print(f"{c['id']} {c['label']:<16} 下单 {c['ordered']}  到货 {expected}{'' if c['arrived'] else '（预计）'}"
              f"  {len(merged):>2} 个产品  {int(total_qty):>5} 桶  ${total_cost:>10,.0f}"
              f"  | Excel 合计 {xl_qty if xl_qty is not None else '-'} 桶 ${xl_cost if xl_cost is not None else '-'}"
              f"  {'OK' if ok else '<-- 不一致'}")

    purchased = {row[1] for row in purchase_items}
    checks = [line for line in checks if line.split("：")[0] in purchased]
    products = []
    for sku, name, size, brand, aliases in CATALOG:
        p = latest_price.get(sku)
        if p is None and sku in EARLY_STOCK_SKUS:  # 早期货柜进的货：采购文件缺失，进价未知
            p = {"cost": 0.0, "freight": 0.0, "price": 0.0, "floor": 0.0}
            checks.append(f"{sku}：早期货柜进的货，采购文件缺失，进价和售价暂记 0")
        # 从没进过货、也没有正式报价的产品（例如第一柜里数量为 0 的 Emerald）不进目录
        if p is None or (sku not in purchased and not isinstance(p["price"], (int, float))):
            continue
        landed = p["cost"] + p["freight"]
        price = p["price"] if isinstance(p["price"], (int, float)) else round(landed * 1.5, 2)
        floor = p["floor"] if isinstance(p["floor"], (int, float)) else round(landed * 1.4, 2)
        if not isinstance(p["price"], (int, float)):
            checks.append(f"{sku}：没有建议售价，按到岸成本 ×1.5 / ×1.4 估算")
        products.append((sku, brand, name, size, "unit", p["cost"], p["freight"], round(price, 2), round(floor, 2),
                         0, LEAD_TIME_DAYS, SUPPLIER[0], "|".join(a for a in aliases if norm(a) != norm(name)), 1))

    def write(name, header, rows):
        with (REAL_DIR / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write("suppliers", ["id", "name", "country", "default_lead_time_days"], [SUPPLIER])
    write("products", ["sku", "brand", "name", "size", "unit", "cost_usd", "freight_usd", "price_usd",
                       "floor_price_usd", "safety_stock", "lead_time_days", "supplier_id", "aliases", "active"], products)
    write("purchases", ["id", "supplier_id", "order_date", "expected_date", "received_date", "status", "note"], purchases)
    write("purchase_items", ["purchase_id", "sku", "qty", "unit_cost", "freight_per_unit"], purchase_items)

    print(f"\n已写入 {REAL_DIR}：{len(products)} 个产品，{len(purchases)} 个货柜，{len(purchase_items)} 行采购明细")
    print("安全库存暂时为 0，等导入销售数据后按日均销量计算。")
    if checks:
        print("\n估算项（不是 Excel 里的原始数字）：")
        for line in checks:
            print(f"  - {line}")


if __name__ == "__main__":
    main()
