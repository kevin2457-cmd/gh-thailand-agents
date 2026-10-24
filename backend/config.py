"""项目配置：路径、.env 读取、模型常量。

.env 的读取顺序：先读仓库文件夹，再读上一层文件夹（课程要求）。
load_dotenv 默认不覆盖已设置的变量，所以仓库文件夹里的值优先。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
REAL_DIR = DATA_DIR / "real"
DB_PATH = DATA_DIR / "app.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
EVIDENCE_DIR = ROOT_DIR / "output" / "evidence"

ENV_FILES = [ROOT_DIR / ".env", ROOT_DIR.parent / ".env"]
for _env in ENV_FILES:
    load_dotenv(_env)

# 课程要求：只用 gpt-6-luna，经 Portkey 调用；不允许用环境变量改成别的模型
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# 课程要求 .env 里只能有 PORTKEY_API_KEY / OPENAI_API_KEY，所以数据源用命令行参数 --source 切换，不放进 .env
DEFAULT_DATA_SOURCE = "sample"


def env_file_found() -> Path | None:
    """返回第一个存在的 .env 路径（用于启动时提示），都没有就返回 None。"""
    return next((p for p in ENV_FILES if p.exists()), None)


def get_portkey_key() -> str:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key or key == "your-portkey-api-key-here":
        raise RuntimeError(
            "缺少 PORTKEY_API_KEY：请把 .env.example 复制为 .env 并填入 key，"
            "放在仓库文件夹或上一层文件夹。"
        )
    return key


def data_dir_for(source: str) -> Path:
    if source == "sample":
        return SAMPLE_DIR
    if source == "real":
        return REAL_DIR
    raise ValueError(f"未知数据源 {source!r}，只能是 sample 或 real")
