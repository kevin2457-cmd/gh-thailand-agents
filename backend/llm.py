"""模型连接（gpt-6-luna 经 Portkey）和 token 计量。

每次 /responses 请求的原始 usage 都由 httpx 钩子记下，并标上当时是哪个 agent 在运行，
运行结束后写进 llm_usage 表。这些就是 Tokenomics 的实测数据。
"""
from __future__ import annotations

import contextvars
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

import httpx
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from backend.config import MODEL_NAME, PORTKEY_BASE_URL, PRICES_PER_1M, get_portkey_key

current_agent: contextvars.ContextVar[str] = contextvars.ContextVar("current_agent", default="?")
_sink: contextvars.ContextVar[list[dict] | None] = contextvars.ContextVar("usage_sink", default=None)


async def _capture_usage(response: httpx.Response) -> None:
    sink = _sink.get()
    if sink is None or not response.url.path.endswith("/responses"):
        return
    await response.aread()
    try:
        body = response.json()
    except ValueError:
        body = {}
    sink.append({"agent": current_agent.get(), "status": response.status_code, "usage": body.get("usage") or {}})


_model: OpenAIResponsesModel | None = None


def get_model() -> OpenAIResponsesModel:
    global _model
    if _model is None:
        key = get_portkey_key()
        client = AsyncOpenAI(
            base_url=PORTKEY_BASE_URL,
            api_key=key,
            default_headers={"x-portkey-api-key": key, "x-portkey-provider": "openai"},
            http_client=httpx.AsyncClient(timeout=120, event_hooks={"response": [_capture_usage]}),
            max_retries=1,
        )
        # gpt-6-luna 的函数工具需要走 Responses API
        _model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    return _model


def cost_of(usage: dict[str, Any]) -> dict[str, Any]:
    """input_tokens 已包含 cached_tokens；output_tokens 已包含 reasoning_tokens。"""
    inp = usage.get("input_tokens", 0) or 0
    out = usage.get("output_tokens", 0) or 0
    cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0
    cost = ((inp - cached) * PRICES_PER_1M["input"] + cached * PRICES_PER_1M["cached_input"]
            + out * PRICES_PER_1M["output"]) / 1_000_000
    return {"input_tokens": inp, "cached_tokens": cached, "output_tokens": out, "cost_usd": cost}


class UsageRecorder:
    """with UsageRecorder(conn, run_id) as rec: ... 运行结束后把每个请求的 usage 写进 llm_usage。"""

    def __init__(self, conn: sqlite3.Connection, run_id: str):
        self.conn, self.run_id, self.rows = conn, run_id, []

    def __enter__(self) -> "UsageRecorder":
        self._token = _sink.set(self.rows)
        return self

    def __exit__(self, *exc) -> None:
        _sink.reset(self._token)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for r in self.rows:
            c = cost_of(r["usage"])
            self.conn.execute(
                "INSERT INTO llm_usage (ts, run_id, agent, model, input_tokens, cached_tokens, output_tokens, "
                "requests, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
                (ts, self.run_id, r["agent"], MODEL_NAME, c["input_tokens"], c["cached_tokens"], c["output_tokens"],
                 c["cost_usd"]))
        self.conn.commit()

    def summary(self) -> dict[str, Any]:
        per_agent: dict[str, dict] = {}
        for r in self.rows:
            c = cost_of(r["usage"])
            a = per_agent.setdefault(r["agent"], {"requests": 0, "input_tokens": 0, "cached_tokens": 0,
                                                  "output_tokens": 0, "cost_usd": 0.0})
            a["requests"] += 1
            for k in ("input_tokens", "cached_tokens", "output_tokens", "cost_usd"):
                a[k] += c[k]
        total = {k: sum(a[k] for a in per_agent.values())
                 for k in ("requests", "input_tokens", "cached_tokens", "output_tokens", "cost_usd")}
        return {"run_id": self.run_id, "total": total, "per_agent": per_agent}
