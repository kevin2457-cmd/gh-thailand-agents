"""在后台的一个固定事件循环里运行 agent。

Dash 的回调跑在普通线程里。模型客户端（httpx.AsyncClient）绑定在第一次使用它的事件循环上，
所以所有 agent 调用都提交到同一个后台循环，而不是每次 asyncio.run() 新建一个循环。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine

_loop: asyncio.AbstractEventLoop | None = None
_lock = threading.Lock()


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    with _lock:
        if _loop is None:
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, name="agent-loop", daemon=True).start()
    return _loop


def run(coro: Coroutine[Any, Any, Any], timeout: float = 240) -> Any:
    return asyncio.run_coroutine_threadsafe(coro, _get_loop()).result(timeout=timeout)
