"""标准产品目录：每个产品一个标准 SKU，加上所有已知写法和中文俗称。

采购导入、盘点导入和录单 agent 都用这里的映射。统计只用标准 SKU，所以一个新写法
必须先加进 aliases（并和老板确认），否则导入会停下来，不会去猜。
产品名、品牌、俗称不是敏感信息，可以提交；进价和销量只在 data/real/。
"""
from __future__ import annotations

import re

# sku, 标准英文名, 规格, 品牌, 其他写法和中文俗称
# 名称和品牌按老板提供的产品照片核对过（data/real/raw/product_photos/，包括 Product_Photos_12_Items.pdf）。
# 规格按采购 Excel：老板确认绝大多数产品卖的是最大规格（CloneX 除外，都是 1L），照片上的规格不算数
CATALOG: list[tuple[str, str, str, str, list[str]]] = [
    # GH FloraPro 25lb 粉剂。采购 Excel 里写成 GH-Grow/Bloom/Core/Late-25lb，"Core" 就是 Calcium + Micros
    # 老板确认：按袋子颜色叫，三色粉 = 红 Bloom / 绿 Grow / 黑 Calcium+Micros，"花" = Late Bloom
    # （单字 红/绿/黑/花 只在"三色粉"上下文里有意义，不放进全局别名，由录单 agent 结合上下文判断）
    ("FP-GROW-25LB", "FloraPro Grow", "25lb", "General Hydroponics", ["GH-Grow-25lb", "绿色粉", "绿粉", "绿色粉 Grow"]),
    ("FP-BLOOM-25LB", "FloraPro Bloom", "25lb", "General Hydroponics",
     ["GH-Bloom-25lb", "红色粉", "红粉", "红 Bloom", "红色粉 Bloom", "FloraBloom"]),  # 老板确认 FloraBloom 就是它
    # 老板确认：10 月表的 GH-Micro-25lb 是 typo，就是 Core
    ("FP-CAMICRO-25LB", "FloraPro Calcium + Micros", "25lb", "General Hydroponics",
     ["GH-Core-25lb", "GH-Micro-25lb", "FloraPro Calcium Micros", "黑色粉", "黑粉", "黑 Micro", "黑色 Micro"]),
    ("FP-LATEBLOOM-25LB", "FloraPro Late Bloom", "25lb", "General Hydroponics",
     ["GH-Late-25lb", "Late Bloom", "红 Late Bloom"]),
    # Athena Pro 系列
    ("ATH-PRO-GROW-25LB", "Athena Pro Grow", "25lb", "Athena", ["Pro-Grow-25lb", "Pro Grow", "Athena Grow"]),
    ("ATH-PRO-BLOOM-25LB", "Athena Pro Bloom", "25lb", "Athena", ["Pro-Bloom-25lb", "Pro Bloom", "Athena Bloom"]),
    ("ATH-PRO-CORE-25LB", "Athena Pro Core", "25lb", "Athena", ["Pro-Core-25lb", "Pro Core", "Athena Core"]),
    ("ATH-BALANCE-25LB", "Athena Pro Balance", "25lb", "Athena", ["Balance 25lb", "Balance powder", "Athena Balance"]),
    ("ATH-CLEANSE-5G", "Athena Cleanse", "5G", "Athena", ["Cleanse 5G", "Cleanse-5Gallon", "Athena Cleanse"]),
    ("ATH-FADE-5G", "Athena Fade", "5G", "Athena", ["Fade 5G", "Fade-5Gallon", "Athena Fade"]),
    ("ATH-CUTS-14OZ", "Athena Cuts", "14oz", "Athena", ["Cuts-14OZ", "Cuts 14oz", "Cuts"]),
    ("TRISHIELD-1G", "Trishield", "1G", "General Hydroponics", ["Trishield 1G", "Trishield 1 gal"]),
    ("TRISHIELD-5G", "Trishield", "5G", "General Hydroponics", ["Trishield 5G"]),
    # 老板确认：Green J - 1L 就是 Green Juice；pH Up/Down 和 Advance 是同一个
    ("GREEN-JUICE-1L", "Green Juice", "1L", "", ["Green Juice", "Green J - 1L"]),
    ("PH-UP", "pH Up", "", "Advanced Nutrients", ["PH UP", "PH UP Advance"]),
    ("PH-DOWN", "pH Down", "", "Advanced Nutrients", ["PH Down", "PH Down Advance"]),
    # Advanced Nutrients
    ("AN-CARBOLOAD", "Carboload", "", "Advanced Nutrients", ["Carboload"]),
    ("AN-OVERDRIVE-6GAL", "Overdrive", "6gal", "Advanced Nutrients", ["Overdrive", "Overdrive 6 gal"]),
    ("AN-BIG-BUD", "Big Bud", "", "Advanced Nutrients", ["Big Bud", "Bigbud"]),
    ("AN-B52", "B-52", "", "Advanced Nutrients", ["B52", "B 52"]),
    ("AN-BUD-CANDY", "Bud Candy", "", "Advanced Nutrients", ["Bud Candy", "棉花糖"]),
    # 老板确认：CloneX 都是 1L（10 月表写的 1 Gal 也是 1L）
    ("CLONEX-1L", "CloneX", "1L", "Growth Technology", ["CloneX", "CloneX 1 Gal", "CloneX GEL - 1L", "CloneX Gel"]),
    ("ORIGINAL-1L", "Original Liquid Plant Fertilizer", "1L", "", ["Original - 1L", "Original"]),
    # 老板确认：Koolbloom 有液体和粉两种，lb 是粉，Gal 是液体。2/4 月表没写规格的是 6gal 液体
    ("GH-KOOLBLOOM-6GAL", "Liquid KoolBloom", "6gal", "General Hydroponics",
     ["Koolbloom", "Liquid Koolbloom", "Liquid Kool bloom 6 gal", "Koolbloom 液体", "Koolbloom 6gal"]),
    ("GH-KOOLBLOOM-16LB", "Dry KoolBloom", "16lb", "General Hydroponics",
     ["Koolbloom 粉 16lb", "Koolbloom 粉", "Dry Koolbloom"]),
    ("CYCO-SUPA-STIKY-5G", "Cyco Supa Stiky", "5G", "Cyco",
     ["Cyco Supa Sticky", "Supa Sticky", "(CYCO) supa sticky 5 gal", "Cyco 糖"]),
    ("GROTEK-MONSTER-BLOOM", "Monster Bloom", "", "Grotek", ["Monster Bloom", "Monster", "紫粉", "三朵花"]),
    # 老板确认：同名的都是同规格，盘点里的 Weight Max 10kg 合并进来
    ("GROTEK-WEIGHTMAX", "WeightMax", "", "Grotek", ["Weight Max", "WeightMax", "Weight Max 10kg", "鸦片粉"]),
    ("BOTANICARE-CALMAG-PLUS-6GAL", "Cal-Mag Plus", "6gal", "Botanicare", ["Cal Mg Plus", "Cal Mg", "Cal mag", "Cal Mag", "番茄", "番茄水"]),
    # 根水：聊天截图里 客户C 群 "Bioroot 3桶 3*280" 和客户A群 "根水 3 3*280" 同价，按 BioRoot 处理（待老板最后确认）
    ("GO-BIOROOT-6GAL", "BioRoot", "6gal", "General Organics", ["Bioroot", "Bio root", "Bio root 6 gal", "Biroot", "根水"]),
    # 老板确认：Floralicious 有 6gal 和 1gal 两种（没有 2.5gal）。采购 Excel 里的是最大规格 6gal；
    # 1gal 是早期货柜进的。只写 "Floralicious" 或 "香味" 有歧义，要问清规格
    ("GH-FLORALICIOUS-PLUS-6GAL", "Floralicious Plus", "6gal", "General Hydroponics",
     ["Floralicious 6 gal", "Floralicious 6gal"]),
    ("GH-FLORALICIOUS-PLUS-1GAL", "Floralicious Plus", "1gal", "General Hydroponics",
     ["Floralicious 1 gal", "Floralicious 1gal"]),
    ("SUPERTHRIVE-PRO-TEKT", "Pro-TeKt", "", "SUPERthrive", ["Pro-Tekt", "Pro Tekt", "Pro tskt"]),
    ("ZEROTOL-2.5G", "ZeroTol 2.0", "2.5G", "BioSafe Systems", ["Zero 2.5G", "Zero", "ZeroTol"]),
    ("SANIDATE-5G", "SaniDate 5.0", "5G", "BioSafe Systems", ["SanDate 5G", "SanDate", "SaniDate"]),
    ("TERPINATOR", "Terpinator", "", "", ["Terpinator"]),
    ("EMERALD", "Emerald", "", "", ["Emerald"]),
    # 早期货柜进的货（老板确认；那段采购文件缺失，所以没有进价）
    ("BIG-TIME-ENZYME", "Big Time Enzyme", "", "Big Time Hydroponics", ["Big time enzyme"]),
    ("BOTANICARE-SILICA-BLAST", "Silica Blast", "", "Botanicare", ["Silica blast"]),
    ("GH-DIAMOND-NECTAR", "Diamond Nectar", "", "General Hydroponics", ["Diamond nectar"]),
    ("GH-TRUEFLO", "TrueFlo", "", "General Hydroponics", ["True flo", "TrueFlo"]),
    ("BLOOM-LIQUID-PLANT-FOOD", "Bloom Liquid Plant Food", "", "Dyna-Gro", ["Bloom liquid plant food"]),
    # 6.26 销售单里的 "Bush load"（照片标签上的品牌是 Wet Inc）；盘点里没有，已卖完
    ("BUSH-LOAD", "Bush Load", "1qt", "Wet Inc", ["Bush load"]),
    ("CYCO-SILICA-5G", "Cyco Silica", "5G", "Cyco", ["CYCO ( silica ) 5 gal", "Cyco silica"]),
]

# 早期货柜进的货：没有采购记录，但盘点里有，所以也要进产品目录
EARLY_STOCK_SKUS = {"GH-FLORALICIOUS-PLUS-1GAL", "BUSH-LOAD", "BIG-TIME-ENZYME", "BOTANICARE-SILICA-BLAST", "GH-DIAMOND-NECTAR", "GH-TRUEFLO",
                    "BLOOM-LIQUID-PLANT-FOOD", "CYCO-SILICA-5G"}


def norm(name: str) -> str:
    """去掉空格、横线、下划线、括号和句点，转小写：'( CYCO) supa sticky 5 gal' -> 'cycosupasticky5gal'。"""
    return re.sub(r"[\s\-_().。]+", "", str(name)).lower()


# 同一个名字有几种规格（例如 Trishield 1G / 5G）时，只写名字是有歧义的：必须带规格才能匹配
_NAME_SKUS: dict[str, list[str]] = {}
for _sku, _name, _size, _brand, _aliases in CATALOG:
    _NAME_SKUS.setdefault(norm(_name), []).append(_sku)
AMBIGUOUS: dict[str, list[str]] = {k: v for k, v in _NAME_SKUS.items() if len(v) > 1}
# 有歧义的俗称和写法（不带规格）：例如 "香味" 可能是 6gal 也可能是 1gal
for _a, _skus in {"Floralicious": ["GH-FLORALICIOUS-PLUS-6GAL", "GH-FLORALICIOUS-PLUS-1GAL"],
                  "香味": ["GH-FLORALICIOUS-PLUS-6GAL", "GH-FLORALICIOUS-PLUS-1GAL"],
                  "向日葵": ["GH-FLORALICIOUS-PLUS-6GAL", "GH-FLORALICIOUS-PLUS-1GAL"],
                  # 杀虫剂 = Trishield（产品照片上写着"杀除昆虫"），但有 1G 和 5G 两种
                  "杀虫剂": ["TRISHIELD-1G", "TRISHIELD-5G"]}.items():
    AMBIGUOUS[norm(_a)] = _skus

ALIAS_TO_SKU: dict[str, str] = {}
for _sku, _name, _size, _brand, _aliases in CATALOG:
    _keys = _aliases + [f"{_name} {_size}"] + ([] if norm(_name) in AMBIGUOUS else [_name])
    for _a in _keys:
        _k = norm(_a)
        if _k in AMBIGUOUS:
            raise ValueError(f"别名 {_a!r} 有歧义（{AMBIGUOUS[_k]}），要带规格")
        if _k in ALIAS_TO_SKU and ALIAS_TO_SKU[_k] != _sku:
            raise ValueError(f"别名 {_a!r} 同时指向 {ALIAS_TO_SKU[_k]} 和 {_sku}")
        ALIAS_TO_SKU[_k] = _sku


# 只在特定上下文里有意义的短名字（老板确认的规则，和 prompts/intake.md 里的说明一致）
_ATHENA_CONTEXT = re.compile(r"athena|8500|8900|13000", re.I)
_ATHENA_SHORT = {"grow": "ATH-PRO-GROW-25LB", "bloom": "ATH-PRO-BLOOM-25LB", "core": "ATH-PRO-CORE-25LB",
                 "balance": "ATH-BALANCE-25LB", "fade": "ATH-FADE-5G", "cleanse": "ATH-CLEANSE-5G"}
_TRICOLOR_SHORT = {"红": "FP-BLOOM-25LB", "绿": "FP-GROW-25LB", "黑": "FP-CAMICRO-25LB", "花": "FP-LATEBLOOM-25LB"}


def context_lookup(raw_name: str, order_text: str) -> str | None:
    """ATHENA 订单里的 Grow/Bloom/Core……= Athena Pro；三色粉订单里的 红/绿/黑/花 = FloraPro。其他情况返回 None。"""
    k = norm(raw_name)
    k = re.sub(r"(25lb|5g|包|桶|bags?|tons?|x)$", "", k)
    if k in _ATHENA_SHORT and _ATHENA_CONTEXT.search(order_text):
        return _ATHENA_SHORT[k]
    if k in _TRICOLOR_SHORT and "三色" in order_text:
        return _TRICOLOR_SHORT[k]
    return None


def lookup(raw_name: str) -> str | None:
    """返回标准 SKU；不认识或有歧义时返回 None（调用方要报错或让人确认，不能猜）。"""
    return ALIAS_TO_SKU.get(norm(raw_name))


def candidates(raw_name: str) -> list[str]:
    """有歧义的名字返回所有候选 SKU，例如 'Trishield' -> ['TRISHIELD-1G', 'TRISHIELD-5G']。"""
    sku = lookup(raw_name)
    return [sku] if sku else AMBIGUOUS.get(norm(raw_name), [])
