"""产品目录：中文俗称、写法变体、有歧义的名字。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.catalog import candidates, lookup  # noqa: E402


def test_chinese_nicknames():
    assert lookup("紫粉") == "GROTEK-MONSTER-BLOOM"
    assert lookup("鸦片粉") == "GROTEK-WEIGHTMAX"
    assert lookup("棉花糖") == "AN-BUD-CANDY"
    assert lookup("三朵花") == "GROTEK-MONSTER-BLOOM"


def test_floralicious_needs_size():
    # 老板确认有 6gal 和 1gal 两种，"香味" 不带规格时不能猜
    assert lookup("香味") is None
    assert candidates("香味") == ["GH-FLORALICIOUS-PLUS-6GAL", "GH-FLORALICIOUS-PLUS-1GAL"]
    assert lookup("Floralicious 1 gal") == "GH-FLORALICIOUS-PLUS-1GAL"


def test_spelling_variants():
    assert lookup("Bigbud") == lookup("Big Bud") == "AN-BIG-BUD"
    assert lookup("B 52.") == "AN-B52"
    assert lookup("( CYCO) supa sticky 5 gal") == "CYCO-SUPA-STIKY-5G"
    assert lookup("GH-Micro-25lb") == "FP-CAMICRO-25LB"


def test_ambiguous_name_is_not_guessed():
    assert lookup("Trishield") is None
    assert candidates("Trishield") == ["TRISHIELD-1G", "TRISHIELD-5G"]
    assert lookup("Trishield 5G") == "TRISHIELD-5G"


def test_unknown_name():
    assert lookup("Bush load") is None
    assert candidates("Bush load") == []
