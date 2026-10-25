"""把真实销售（Word 销售报告 + 微信截图里的订单）逐单交给录单 agent，进入待审批队列。

每一单都和员工在页面上录单走同一条路：脱敏 -> 录单 agent -> 代码校验 -> 待审批。老板在页面上批准后才写入。
输入：data/real/raw/sales_report/*.docx + data/real/screenshot_orders.json（都 gitignored，只在老板电脑上）
输出：data/real.db 的 pending_records；运行记录存到 output/evidence/real_sales_import.json（gitignored）

客户：老板 10/24 决定，报告里没标客户的订单记为"未标注客户"（UNLABELED），不猜。
报告里有两单用聊天记录的版本代替（报告把其中一单的 Weight Max 记成 2 桶，聊天和银行转账都是 1 桶）。

用法：python scripts/import_real_sales.py        （先运行 init_db.py --source real）
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import intake  # noqa: E402
from backend.config import EVIDENCE_DIR, REAL_DIR, UNLABELED_CODE, db_path_for, set_active_db  # noqa: E402
from backend.db import connect  # noqa: E402
from backend.orders import ensure_customer  # noqa: E402

REPORT = next((REAL_DIR / "raw" / "sales_report").glob("*.docx"))
TODAY = date(2026, 10, 24)
YEAR = 2026

# 客户名和从聊天截图里抄下的订单是真实的私人数据：放在 gitignored 的 data/real/screenshot_orders.json，
# 格式 {"report_customers": {报告订单键: 客户名}, "report_skip": {报告订单键: 原因},
#       "customers": {客户名: 地区}, "screenshot_orders": [{"customer", "date", "text"}]}
PRIVATE = json.loads((REAL_DIR / "screenshot_orders.json").read_text(encoding="utf-8"))
REPORT_CUSTOMERS = PRIVATE["report_customers"]
REPORT_SKIP = PRIVATE["report_skip"]
CUSTOMERS = PRIVATE["customers"]
SCREENSHOT_ORDERS = [(o["customer"], o["date"], o["text"]) for o in PRIVATE["screenshot_orders"]]

HEADER = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\s*(日)?\s*(订单|单|结算)")
SUB = re.compile(r"^\s*(\d)\.\s*(ATHENA|[A-Za-z一-鿿])")


def split_report() -> list[dict]:
    """按日期标题切开销售报告；6.25 那天有 5 个子订单。保留每单的完整原文（包括合计行）。"""
    lines = [p.text.strip() for p in docx.Document(REPORT).paragraphs if p.text.strip()]
    orders, cur = [], None
    for t in lines:
        m = HEADER.match(t)
        if m:
            cur = {"key": f"{m.group(1)}.{m.group(2)}", "date": f"{YEAR}-{int(m.group(1)):02d}-{int(m.group(2)):02d}",
                   "lines": [t]}
            orders.append(cur)
            continue
        if cur is None:
            continue
        s = SUB.match(t)
        if s and cur["key"].startswith("6.25"):
            if cur["key"] == "6.25" and len(cur["lines"]) == 1:  # 第 1 个子订单：沿用标题
                cur["key"] = "6.25 第1单"
            else:
                cur = {"key": f"6.25 第{s.group(1)}单", "date": cur["date"], "lines": []}
                orders.append(cur)
            cur["lines"].append(t[s.end(1) + 1:].strip())
            continue
        if set(t) <= set("—-_ "):
            continue
        if cur["key"].startswith("6.25 第") and t.startswith("总计"):
            continue  # 6.25 最后一行是当天 5 单的合计，不属于第 5 单
        cur["lines"].append(t)
    return [o for o in orders if len(o["lines"]) > 1 or o["key"].startswith("6.25")]


async def run_one(sem: asyncio.Semaphore, job: dict) -> dict:
    async with sem:
        t0 = time.perf_counter()
        hint = (f"Order date: {job['date']}. Source: {job['source_label']}. Prices: Athena in Thai Baht; "
                f"US-brand additives usually in USD.")
        try:
            r = await intake(job["text"], customer_code=job["customer_code"], submitted_by="U02",
                             source_type=job["source_type"], today=TODAY, hint=hint)
            r["seconds"] = round(time.perf_counter() - t0, 1)
            return {**job, "ok": True, "result": r}
        except Exception as e:  # 一单失败不影响其他单
            return {**job, "ok": False, "error": f"{type(e).__name__}: {e}"}


async def main() -> None:
    db = db_path_for("real")
    set_active_db(db)
    conn = connect(db)
    codes = {name: ensure_customer(conn, name, region=region, created="2026-06-01") for name, region in CUSTOMERS.items()}
    codes[UNLABELED_CODE] = ensure_customer(conn, UNLABELED_CODE, region="unknown", created="2026-06-01")
    conn.close()

    jobs = []
    for o in split_report():
        if o["key"] in REPORT_SKIP:
            continue
        name = REPORT_CUSTOMERS.get(o["key"], UNLABELED_CODE)
        jobs.append({"key": f"报告 {o['key']}", "date": o["date"], "customer_code": codes[name],
                     "source_type": "report", "source_label": "owner's Word sales report", "text": "\n".join(o["lines"])})
    for name, d, text in SCREENSHOT_ORDERS:
        jobs.append({"key": f"截图 {name} {d}", "date": d, "customer_code": codes[name], "source_type": "wechat",
                     "source_label": "WeChat chat with the customer", "text": text})
    print(f"共 {len(jobs)} 单，开始逐单解析（并发 4）……")

    t0 = time.perf_counter()
    sem = asyncio.Semaphore(4)
    results = await asyncio.gather(*(run_one(sem, j) for j in jobs))
    elapsed = time.perf_counter() - t0

    ok = [r for r in results if r["ok"]]
    cost = sum(r["result"]["usage"]["total"]["cost_usd"] for r in ok)
    inp = sum(r["result"]["usage"]["total"]["input_tokens"] for r in ok)
    cached = sum(r["result"]["usage"]["total"]["cached_tokens"] for r in ok)
    out = sum(r["result"]["usage"]["total"]["output_tokens"] for r in ok)
    blocked = [r for r in ok if r["result"]["checked"]["blocking"]]
    warned = [r for r in ok if r["result"]["checked"]["warnings"] and not r["result"]["checked"]["blocking"]]
    print(f"完成 {len(ok)}/{len(jobs)} 单，用时 {elapsed:.0f} 秒；输入 {inp:,}（缓存 {cached:,}），输出 {out:,}，"
          f"费用 ${cost:.4f}（平均每单 ${cost / max(len(ok), 1):.5f}）")
    print(f"  必须老板处理：{len(blocked)} 单；有警告：{len(warned)} 单；干净：{len(ok) - len(blocked) - len(warned)} 单")
    for r in results:
        if not r["ok"]:
            print(f"  失败 {r['key']}: {r['error']}")
    for r in blocked:
        print(f"  [必须处理] {r['key']}: {'；'.join(r['result']['checked']['blocking'])[:160]}")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / "real_sales_import.json"
    path.write_text(json.dumps({"elapsed_seconds": round(elapsed, 1), "orders": len(jobs), "ok": len(ok),
                                "cost_usd": cost, "input_tokens": inp, "cached_tokens": cached, "output_tokens": out,
                                "results": results}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("已保存", path)


if __name__ == "__main__":
    asyncio.run(main())
