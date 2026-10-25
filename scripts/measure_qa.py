"""跑一组典型的老板问题，测问答（协调 agent + 专家 agent）的 token 和费用。

用法：python scripts/measure_qa.py                # 模拟数据 data/app.db
      python scripts/measure_qa.py --data real    # 真实数据 data/real.db（结果存为 real_ 开头，不提交）
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import ask  # noqa: E402
from backend.config import EVIDENCE_DIR, db_path_for, set_active_db  # noqa: E402

QUESTIONS = [
    "哪些产品需要马上补货？",
    "下一个货柜（大约 60 天后到）应该多订哪些产品？",
    "哪些老客户很久没下单了？",
    "最近 30 天卖得最好的 5 个产品是什么，销售额多少？",
    "给最久没下单的客户写一条跟进话术。",
    "Monster Bloom 还剩多少？会不会在下一批货到之前断货？",
]


async def main(data: str) -> None:
    set_active_db(db_path_for(data))
    out = []
    for q in QUESTIONS:
        t0 = time.perf_counter()
        r = await ask(q, today=date.today())
        sec = round(time.perf_counter() - t0, 1)
        u = r["usage"]["total"]
        out.append({"question": q, "seconds": sec, "answer": r["answer"], "tools": [(t["agent"], t["tool"])
                                                                                   for t in r["trace"]],
                    "usage": r["usage"]})
        print(f"{sec:>5}s  {u['requests']} req  in {u['input_tokens']:,} (cached {u['cached_tokens']:,})  "
              f"out {u['output_tokens']:,}  ${u['cost_usd']:.5f}  {q}")
    name = ("real_" if data == "real" else "") + "qa_runs.json"
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", choices=["sample", "real"], default="sample")
    asyncio.run(main(ap.parse_args().data))
