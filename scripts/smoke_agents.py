"""用真模型跑一次录单和一次问答，打印结果和 token 用量，并存进 output/evidence/。

用法：python scripts/smoke_agents.py            # 用当前 data/app.db（默认是模拟数据）
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import ask, intake  # noqa: E402
from backend.config import EVIDENCE_DIR  # noqa: E402

TODAY = date(2026, 10, 23)

# 模拟的微信订单（格式照老板的真实订单写法：三色粉、折扣、美金折合泰铢，里面故意有一个算错的小计）
ORDER_TEXT = """10月5日 订单统计：
三色（63折）
绿色粉5：120*3=360
黑色粉15：120*15=1800
红色粉：10*120=1200
Big bud：600
番茄水：220
合计：4180*0.63=2633.4美金
折合：88700泰铢
运费到付"""

QUESTION = "哪些产品需要马上补货？另外哪些老客户很久没下单了，给最久没下单的那位写一条跟进话术。"


async def main() -> None:
    out = {}
    r = await intake(ORDER_TEXT, customer_code="CUST-012", submitted_by="U02", today=TODAY)
    out["intake"] = r
    print("== 录单 agent ==")
    print("待审批编号:", r["pending_id"])
    for l in r["checked"]["lines"]:
        print(f"  {l['product_text']:<8} -> {l['sku']}  qty={l['qty']} price={l['unit_price']} {l['currency']} "
              f"x{l['discount']}  usd/unit={l.get('unit_price_usd')}")
    print("  警告:", r["checked"]["warnings"])
    print("  必须处理:", r["checked"]["blocking"])
    print("  用量:", json.dumps(r["usage"]["total"]))

    q = await ask(QUESTION, today=TODAY)
    out["ask"] = q
    print("\n== 协调 agent ==")
    print(q["answer"])
    print("  工具调用:", [(t["agent"], t["tool"]) for t in q["trace"]])
    print("  用量:", json.dumps(q["usage"]["per_agent"], ensure_ascii=False))

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / "step3_smoke_sample.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\n已保存", path)


if __name__ == "__main__":
    asyncio.run(main())
