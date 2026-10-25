"""Tokenomics：只用 llm_usage 表里的实测数字（每次模型请求的真实 token），算成本和规模。

用法：python scripts/tokenomics.py [--db data/real.db] [--db data/app.db]
输出：output/evidence/tokenomics.json 和 tokenomics.md（只含 token 和美元，不含业务数据）
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DB_PATH, EVIDENCE_DIR, PRICES_PER_1M, REAL_DB_PATH  # noqa: E402

# 使用量假设（老板确认前是估计；报告里会写明）：一个"用户" = 一个录单员工或老板的账号
INTAKES_PER_DAY = 8      # 每个工作日录 8 单
QUESTIONS_PER_DAY = 4    # 每个工作日问 4 个问题
WORKDAYS = 26


def load_runs(paths: list[Path]) -> list[dict]:
    runs = []
    for p in paths:
        if not p.exists():
            continue
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        for r in conn.execute(
                """SELECT run_id, SUM(requests) AS req, SUM(input_tokens) AS inp, SUM(cached_tokens) AS cached,
                          SUM(output_tokens) AS outp, SUM(cost_usd) AS cost FROM llm_usage
                   WHERE input_tokens > 0 GROUP BY run_id"""):
            runs.append({**dict(r), "kind": "intake" if r["run_id"].startswith("intake") else "ask", "db": p.name})
        conn.close()
    return runs


def no_cache_cost(r: dict) -> float:
    return (r["inp"] * PRICES_PER_1M["input"] + r["outp"] * PRICES_PER_1M["output"]) / 1_000_000


def stats(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return {
        "runs": len(rows),
        "requests_per_run": round(mean(r["req"] for r in rows), 2),
        "input_tokens_per_run": round(mean(r["inp"] for r in rows)),
        "cached_tokens_per_run": round(mean(r["cached"] for r in rows)),
        "output_tokens_per_run": round(mean(r["outp"] for r in rows)),
        "cache_hit_rate": round(sum(r["cached"] for r in rows) / max(sum(r["inp"] for r in rows), 1), 3),
        "cost_per_run_mean": mean(r["cost"] for r in rows),
        "cost_per_run_median": median(r["cost"] for r in rows),
        "cost_per_run_without_cache": mean(no_cache_cost(r) for r in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", action="append", type=Path)
    args = ap.parse_args()
    runs = load_runs(args.db or [REAL_DB_PATH, DB_PATH])
    s = {k: stats([r for r in runs if r["kind"] == k]) for k in ("intake", "ask")}
    per_user_month = WORKDAYS * (INTAKES_PER_DAY * s["intake"]["cost_per_run_mean"]
                                 + QUESTIONS_PER_DAY * s["ask"]["cost_per_run_mean"])
    per_user_month_nc = WORKDAYS * (INTAKES_PER_DAY * s["intake"]["cost_per_run_without_cache"]
                                    + QUESTIONS_PER_DAY * s["ask"]["cost_per_run_without_cache"])
    out = {
        "model": "gpt-6-luna", "prices_per_1m_usd": PRICES_PER_1M,
        "assumptions": {"intakes_per_day": INTAKES_PER_DAY, "questions_per_day": QUESTIONS_PER_DAY,
                        "workdays_per_month": WORKDAYS},
        "measured": s,
        "per_user_per_month_usd": per_user_month,
        "per_user_per_month_without_cache_usd": per_user_month_nc,
        "scale_usd_per_month": {n: per_user_month * n for n in (1, 3, 100, 10_000)},
        "scale_without_cache_usd_per_month": {n: per_user_month_nc * n for n in (1, 3, 100, 10_000)},
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "tokenomics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    md = ["| Run type | Runs measured | Requests/run | Input tokens/run | Cached/run | Output tokens/run | "
          "Cache hit | Cost/run | Cost/run without cache |", "|---|---|---|---|---|---|---|---|---|"]
    for k, label in (("intake", "Order entry (intake agent)"), ("ask", "Owner Q&A (orchestrator + specialists)")):
        x = s[k]
        md.append(f"| {label} | {x['runs']} | {x['requests_per_run']} | {x['input_tokens_per_run']:,} | "
                  f"{x['cached_tokens_per_run']:,} | {x['output_tokens_per_run']:,} | {x['cache_hit_rate']:.0%} | "
                  f"${x['cost_per_run_mean']:.5f} | ${x['cost_per_run_without_cache']:.5f} |")
    md += ["", f"Per user per month ({INTAKES_PER_DAY} orders + {QUESTIONS_PER_DAY} questions per day, {WORKDAYS} days): "
               f"**${per_user_month:.3f}** (without prompt caching ${per_user_month_nc:.3f})", "",
           "| Users | LLM cost / month | Without caching |", "|---|---|---|"]
    for n in (1, 3, 100, 10_000):
        md.append(f"| {n:,} | ${per_user_month * n:,.2f} | ${per_user_month_nc * n:,.2f} |")
    (EVIDENCE_DIR / "tokenomics.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
