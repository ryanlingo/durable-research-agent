"""Shared model / provider configuration (env-overridable)."""

from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load project-root .env into os.environ if present (does not override)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

# Chat / completion model used for all agent LLM calls
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.6-luna")


def model_supports_temperature(model: str | None = None) -> bool:
    """Some chat models only accept the API default temperature (omit the param)."""
    name = (model or LLM_MODEL).lower()
    # gpt-5.x / o-series style models reject custom temperature values
    if name.startswith("gpt-5") or "luna" in name:
        return False
    if name.startswith("o1") or name.startswith("o3") or name.startswith("o4"):
        return False
    return True


# Embedding model for RAG ("small" → OpenAI text-embedding-3-small)
_EMBEDDING_RAW = os.getenv("EMBEDDING_MODEL", "small").strip().lower()
if _EMBEDDING_RAW in ("small", "3-small", "text-embedding-3-small"):
    EMBEDDING_MODEL = "text-embedding-3-small"
elif _EMBEDDING_RAW in ("large", "3-large", "text-embedding-3-large"):
    EMBEDDING_MODEL = "text-embedding-3-large"
elif _EMBEDDING_RAW in ("ada", "ada-002", "text-embedding-ada-002"):
    EMBEDDING_MODEL = "text-embedding-ada-002"
else:
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
