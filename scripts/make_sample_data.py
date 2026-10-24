"""生成模拟数据集 data/sample/*.csv（固定随机种子，每次结果相同）。

SKU 是真实的 General Hydroponics 产品；客户、订单、价格、库存全部是模拟的。
模拟一年的业务（截至 TODAY），并刻意留下几个演示场景：
  - 几个客户按自己的周期稳定下单，然后突然不再下单（沉睡客户）
  - 几个 SKU 最近没有及时补货，库存接近或低于安全库存（补货提醒）
  - 有采购单还在路上（在途库存）

用法：python scripts/make_sample_data.py
"""
from __future__ import annotations

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import SAMPLE_DIR  # noqa: E402

SEED = 409
TODAY = date(2026, 10, 23)
START = TODAY - timedelta(days=365)

USERS = [
    ("U01", "Kevin (owner)", "owner"),
    ("U02", "Sales staff (sample)", "staff"),
    ("U03", "Warehouse staff (sample)", "staff"),
]

SUPPLIERS = [
    ("S01", "General Hydroponics (USA)", "USA", 35),
    ("S02", "Advanced Nutrients (sample distributor)", "Canada", 21),
]

# sku, brand, name, size, units_per_case, cost_thb/case, price_thb/case, supplier, aliases
PRODUCTS = [
    ("GH-FG-1G", "General Hydroponics", "FloraGro", "1 gal", 4, 3200, 4600, "S01", "Flora Gro|FG|三元A|生长液"),
    ("GH-FM-1G", "General Hydroponics", "FloraMicro", "1 gal", 4, 3200, 4600, "S01", "Flora Micro|FM|三元B|微量元素"),
    ("GH-FB-1G", "General Hydroponics", "FloraBloom", "1 gal", 4, 3200, 4600, "S01", "Flora Bloom|FB|三元C|开花液"),
    ("GH-FG-1Q", "General Hydroponics", "FloraGro", "1 qt", 12, 2700, 3900, "S01", "FloraGro小瓶|FG 1qt"),
    ("GH-FM-1Q", "General Hydroponics", "FloraMicro", "1 qt", 12, 2700, 3900, "S01", "FloraMicro小瓶|FM 1qt"),
    ("GH-FB-1Q", "General Hydroponics", "FloraBloom", "1 qt", 12, 2700, 3900, "S01", "FloraBloom小瓶|FB 1qt"),
    ("GH-CMG-1G", "General Hydroponics", "CALiMAGic", "1 gal", 4, 3600, 5200, "S01", "Cal-Mag|CalMag|钙镁|แคลแมก"),
    ("GH-MB-2.2LB", "General Hydroponics", "Monster Bloom", "2.2 lb", 6, 5400, 7800, "S01", "MB|Monster|开花粉|มอนสเตอร์"),
    ("GH-KB-1Q", "General Hydroponics", "Liquid KoolBloom", "1 qt", 12, 4200, 6000, "S01", "KoolBloom|Kool Bloom|KB|酷开花"),
    ("GH-AS-1Q", "General Hydroponics", "Armor Si", "1 qt", 12, 3000, 4300, "S01", "Armor Si|硅|ซิลิก้า"),
    ("GH-RS-1Q", "General Hydroponics", "RapidStart", "1 qt", 12, 5600, 8000, "S01", "Rapid Start|生根液|เร่งราก"),
    ("GH-FLP-1Q", "General Hydroponics", "Floralicious Plus", "1 qt", 12, 4800, 6900, "S01", "Floralicious|FL+"),
    ("GH-PHU-1Q", "General Hydroponics", "pH Up", "1 qt", 12, 1800, 2600, "S01", "pH Up|调高|pH上"),
    ("GH-PHD-1Q", "General Hydroponics", "pH Down", "1 qt", 12, 1800, 2600, "S01", "pH Down|调低|pH下"),
    ("AN-BB-1L", "Advanced Nutrients", "Big Bud", "1 L", 12, 6000, 8400, "S02", "BigBud|BB|大花"),
]

# 最近没有及时补货的 SKU（演示补货提醒）：从这一天起不再给它们下采购单
STOP_REORDER = {"GH-MB-2.2LB": date(2026, 8, 20), "GH-CMG-1G": date(2026, 9, 1), "GH-KB-1Q": date(2026, 8, 25)}

REGIONS = ["Bangkok", "Bangkok", "Bangkok", "Nonthaburi", "Chiang Mai", "Chiang Mai", "Phuket",
           "Pattaya", "Khon Kaen", "Hua Hin", "Udon Thani", "Nakhon Ratchasima"]
TYPE_WEIGHTS = [("grow_shop", 0.45), ("farm", 0.25), ("reseller", 0.15), ("retail", 0.15)]
DISCOUNT = {"reseller": 0.85, "grow_shop": 0.92, "farm": 0.95, "retail": 1.0}
SIZE = {"reseller": (6, 14), "grow_shop": (2, 6), "farm": (2, 5), "retail": (1, 2)}  # 每个 SKU 每单的箱数范围
CYCLE = {"reseller": (14, 28), "grow_shop": (18, 35), "farm": (25, 45), "retail": (30, 60)}

NAME_A = ["Green", "Siam", "Lotus", "Jungle", "Tropic", "Canopy", "River", "Golden", "Lanna", "Andaman",
          "Orchid", "Bamboo", "Monsoon", "Rice Field", "Mango", "Coconut"]
NAME_B = ["Hydro Shop", "Grow Supply", "Farm", "Garden Center", "Hydroponics", "Agri", "Grow House", "Greens"]
NICKS = ["Nok", "Ben", "Joe", "Ann", "Pim", "Tor", "Bee", "Mai", "Golf", "Beam", "Toon", "Pond", "Fon", "Art", "Ploy", "Tum"]

N_CUSTOMERS = 40
N_DORMANT = 6
N_NEW = 3

# 典型购物篮：一套 Flora 三件 + 几个添加剂
BASKETS = [
    ["GH-FG-1G", "GH-FM-1G", "GH-FB-1G", "GH-CMG-1G"],
    ["GH-FG-1G", "GH-FM-1G", "GH-FB-1G", "GH-MB-2.2LB", "GH-KB-1Q"],
    ["GH-FG-1Q", "GH-FM-1Q", "GH-FB-1Q", "GH-PHD-1Q"],
    ["GH-MB-2.2LB", "GH-CMG-1G", "AN-BB-1L"],
    ["GH-CMG-1G", "GH-AS-1Q", "GH-RS-1Q", "GH-FLP-1Q"],
    ["GH-FB-1G", "GH-MB-2.2LB", "GH-KB-1Q", "GH-PHD-1Q", "GH-PHU-1Q"],
]


THB_PER_USD = 35  # 下面的价格表是按泰铢写的，输出时换算成美元


def usd(thb: float) -> float:
    return round(thb / THB_PER_USD, 2)


def iso(d: date) -> str:
    return d.isoformat()


def write_csv(name: str, header: list[str], rows: list[tuple | list]) -> None:
    path = SAMPLE_DIR / f"{name}.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def make_customers(rng: random.Random) -> list[dict]:
    names: set[str] = set()
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        ctype = rng.choices([t for t, _ in TYPE_WEIGHTS], [w for _, w in TYPE_WEIGHTS])[0]
        region = rng.choice(REGIONS)
        while True:
            name = f"{rng.choice(NAME_A)} {rng.choice(NAME_B)} {region}"
            if name not in names:
                names.add(name)
                break
        basket = list(rng.choice(BASKETS))
        if rng.random() < 0.5:  # 一半客户再加一两个别的产品
            basket += rng.sample([p[0] for p in PRODUCTS if p[0] not in basket], rng.randint(1, 2))
        customers.append({
            "id": f"C{i:03d}",
            "code": f"CUST-{i:03d}",
            "name": f"{name} (sample)",
            "phone": f"000-000-{i:04d}",
            "address": f"Sample address {i}, {region}",
            "wechat_alias": f"{rng.choice(NICKS)}-{name.split()[0]}",
            "region": region,
            "type": ctype,
            "cycle": rng.randint(*CYCLE[ctype]),
            "basket": basket,
            "start": START,
            "stop": None,
        })
    # 沉睡客户：曾经稳定下单的中大客户，在 2–4 个周期前停止下单
    regulars = [c for c in customers if c["type"] in ("reseller", "grow_shop")]
    for c in rng.sample(regulars, N_DORMANT):
        c["stop"] = TODAY - timedelta(days=int(c["cycle"] * rng.uniform(2.0, 4.0)))
    # 新客户：最近两个月才开始下单
    for c in rng.sample([c for c in customers if c["stop"] is None], N_NEW):
        c["start"] = TODAY - timedelta(days=rng.randint(30, 60))
    for c in customers:
        c["created_at"] = iso(c["start"])
    return customers


def make_orders(rng: random.Random, customers: list[dict]) -> dict[date, list[tuple[dict, dict[str, int]]]]:
    """按每个客户的周期生成计划订单：{日期: [(客户, {sku: 箱数})]}。"""
    orders: dict[date, list] = {}
    for c in customers:
        d = c["start"] + timedelta(days=rng.randint(0, c["cycle"]))
        end = c["stop"] or TODAY
        while d <= end:
            items = {}
            for sku in c["basket"]:
                if rng.random() < 0.8:  # 不是每次都买齐
                    items[sku] = rng.randint(*SIZE[c["type"]])
            if items:
                orders.setdefault(d, []).append((c, items))
            d += timedelta(days=max(5, int(rng.gauss(c["cycle"], c["cycle"] * 0.15))))
    return orders


def daily_demand(orders: dict) -> dict[str, float]:
    total: dict[str, int] = {}
    for day_orders in orders.values():
        for _, items in day_orders:
            for sku, q in items.items():
                total[sku] = total.get(sku, 0) + q
    return {p[0]: total.get(p[0], 0) / 365 for p in PRODUCTS}


def main() -> None:
    rng = random.Random(SEED)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    prod = {p[0]: p for p in PRODUCTS}
    lead = {s[0]: s[3] for s in SUPPLIERS}

    customers = make_customers(rng)
    orders = make_orders(rng, customers)
    rate = daily_demand(orders)
    safety = {sku: max(5, round(r * 14)) for sku, r in rate.items()}  # 安全库存 ≈ 两周销量

    # 期初库存：约 60 天的销量
    stock = {sku: round(rate[sku] * 60) + safety[sku] for sku in prod}
    opening = [(sku, iso(START - timedelta(days=1)), q) for sku, q in stock.items()]

    sales, sale_items, purchases, purchase_items = [], [], [], []
    in_transit: list[dict] = []  # {"id", "arrive": date, "items": {sku: qty}}
    so_n = po_n = 0

    day = START
    while day <= TODAY:
        # 1) 到货
        for po in [p for p in in_transit if p["arrive"] <= day]:
            for sku, q in po["items"].items():
                stock[sku] += q
            po["row"][4] = iso(day)
            po["row"][5] = "received"
            in_transit.remove(po)

        # 2) 出货：没有库存的 SKU 只能少发
        for c, items in orders.get(day, []):
            shipped = {sku: min(q, stock[sku]) for sku, q in items.items() if stock[sku] > 0}
            if not shipped:
                continue
            so_n += 1
            sid = f"SO-{so_n:06d}"
            sales.append((sid, iso(day), c["id"], "import", ""))
            for sku, q in shipped.items():
                stock[sku] -= q
                sale_items.append((sid, sku, q, round(prod[sku][6] * DISCOUNT[c["type"]])))

        # 3) 每周一检查补货：库存 + 在途 低于（交期 + 30 天）的销量 + 安全库存，就补到（交期 + 60 天）
        if day.weekday() == 0:
            for sup_id, _, _, sup_lead in SUPPLIERS:
                items = {}
                for sku, p in prod.items():
                    if p[7] != sup_id or (sku in STOP_REORDER and day >= STOP_REORDER[sku]):
                        continue
                    pipeline = stock[sku] + sum(po["items"].get(sku, 0) for po in in_transit)
                    if pipeline < rate[sku] * (sup_lead + 30) + safety[sku]:
                        items[sku] = max(10, round(rate[sku] * (sup_lead + 60) + safety[sku] - pipeline))
                if items:
                    po_n += 1
                    pid = f"PO-{po_n:04d}"
                    arrive = day + timedelta(days=sup_lead + rng.randint(-3, 5))
                    row = [pid, sup_id, iso(day), iso(day + timedelta(days=sup_lead)), "", "ordered", ""]
                    purchases.append(row)
                    for sku, q in items.items():
                        purchase_items.append((pid, sku, q, prod[sku][5]))
                    in_transit.append({"id": pid, "arrive": arrive, "items": items, "row": row})
        day += timedelta(days=1)

    write_csv("users", ["id", "name", "role"], USERS)
    write_csv("suppliers", ["id", "name", "country", "default_lead_time_days"], SUPPLIERS)
    write_csv(
        "products",
        ["sku", "brand", "name", "size", "unit", "cost_usd", "freight_usd", "price_usd", "floor_price_usd",
         "safety_stock", "lead_time_days", "supplier_id", "aliases", "active"],
        [(p[0], p[1], p[2], p[3], "case", usd(p[5]), 0, usd(p[6]), usd(p[6] * 0.93), safety[p[0]], lead[p[7]], p[7],
          p[8], 1) for p in PRODUCTS],
    )
    write_csv(
        "customers",
        ["id", "code", "name", "phone", "address", "wechat_alias", "region", "type", "created_at"],
        [(c["id"], c["code"], c["name"], c["phone"], c["address"], c["wechat_alias"], c["region"], c["type"],
          c["created_at"]) for c in customers],
    )
    write_csv("sales", ["id", "sale_date", "customer_id", "source", "note"], sales)
    write_csv("sale_items", ["sale_id", "sku", "qty", "unit_price"],
              [(sid, sku, q, usd(p)) for sid, sku, q, p in sale_items])
    write_csv("purchases", ["id", "supplier_id", "order_date", "expected_date", "received_date", "status", "note"], purchases)
    write_csv("purchase_items", ["purchase_id", "sku", "qty", "unit_cost", "freight_per_unit"],
              [(pid, sku, q, usd(c), 0) for pid, sku, q, c in purchase_items])
    write_csv("opening_stock", ["sku", "as_of_date", "qty"], opening)

    print(f"已写入 {SAMPLE_DIR}")
    print(f"  客户 {len(customers)}（沉睡 {N_DORMANT}，新客户 {N_NEW}），销售单 {len(sales)}，采购单 {len(purchases)}（在途 {len(in_transit)}）")
    print("  模拟期末库存（箱）/ 安全库存：")
    for sku in prod:
        flag = "  <-- 低于安全库存" if stock[sku] <= safety[sku] else ""
        print(f"    {sku:<12} {stock[sku]:>5} / {safety[sku]:<4}{flag}")


if __name__ == "__main__":
    main()
