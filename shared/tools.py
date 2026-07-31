"""Shared tools: web search (with graceful fallback) and token helpers."""

from __future__ import annotations

import os

from openai import OpenAI

from .config import LLM_MODEL, model_supports_temperature
from .types import SearchResult, TokenUsage


def _mock_search(query: str) -> SearchResult:
    """Deterministic fallback when no search API key is present."""
    content = (
        f"Mock search results for '{query}'. "
        "In a real deployment this would call Tavily, Serper, or Bing. "
        "Key points: durable execution prevents lost intermediate results; "
        "human-in-the-loop should not require polling loops; "
        "evaluation belongs inside the control flow."
    )
    return SearchResult(query=query, content=content, source="mock")


def web_search(query: str) -> SearchResult:
    """Perform a web search. Uses Tavily if TAVILY_API_KEY is set, otherwise mock."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return _mock_search(query)

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        resp = client.search(query=query, max_results=3)
        snippets = []
        for r in resp.get("results", [])[:3]:
            snippets.append(f"- {r.get('title', '')}: {r.get('content', '')[:400]}")
        content = "\n".join(snippets) or _mock_search(query).content
        return SearchResult(query=query, content=content, source="tavily")
    except Exception:
        return _mock_search(query)


def llm_call(
    system: str,
    user: str,
    model: str | None = None,
    temperature: float | None = 0.2,
) -> tuple[str, TokenUsage]:
    client = OpenAI()
    chosen = model or LLM_MODEL
    kwargs: dict = {
        "model": chosen,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if temperature is not None and model_supports_temperature(chosen):
        kwargs["temperature"] = temperature
    resp = client.chat.completions.create(**kwargs)
    usage = TokenUsage()
    if resp.usage:
        usage.prompt_tokens = resp.usage.prompt_tokens
        usage.completion_tokens = resp.usage.completion_tokens
        usage.total_tokens = resp.usage.total_tokens
    text = resp.choices[0].message.content or ""
    return text, usage
