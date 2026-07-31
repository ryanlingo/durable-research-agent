"""Smoke tests for shared configuration."""

from shared.config import EMBEDDING_MODEL, LLM_MODEL, model_supports_temperature


def test_default_models_are_set() -> None:
    assert isinstance(LLM_MODEL, str) and LLM_MODEL
    assert EMBEDDING_MODEL == "text-embedding-3-small" or "embedding" in EMBEDDING_MODEL


def test_gpt5_style_models_omit_temperature() -> None:
    assert model_supports_temperature("gpt-5.6-luna") is False
    assert model_supports_temperature("gpt-4o-mini") is True
