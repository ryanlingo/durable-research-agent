"""Temporal Activities for the research agent.

All non-deterministic work lives here: LLM calls, search, RAG, evaluation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from temporalio import activity

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import (
    evaluate_report,
    llm_call,
    retrieve,
    web_search,
)


@activity.defn
async def clarify_activity(query: str) -> dict[str, Any]:
    system = (
        "You decide whether a research query needs clarification. "
        "If the query is already specific, return {\"needs_clarification\": false}. "
        "If not, return {\"needs_clarification\": true, \"questions\": [..], \"reason\": \"..\"}."
    )
    text, usage = llm_call(system, query, temperature=0.0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"needs_clarification": False}
    data["_tokens"] = usage.to_dict()
    return data


@activity.defn
async def plan_activity(query: str) -> dict[str, Any]:
    system = (
        "Produce 2 or 3 focused web search queries for the given research topic. "
        "Return ONLY a JSON list of strings."
    )
    text, usage = llm_call(system, query)
    try:
        plan = json.loads(text)
        if not isinstance(plan, list):
            plan = [query]
    except json.JSONDecodeError:
        plan = [query, f"{query} recent developments"]
    return {"plan": [str(q) for q in plan[:3]], "_tokens": usage.to_dict()}


@activity.defn
async def retrieve_activity(query: str) -> dict[str, Any]:
    chunks, usage = retrieve(query, k=4)
    return {
        "chunks": [
            {
                "doc_id": c.doc_id,
                "title": c.title,
                "content": c.content,
                "score": c.score,
            }
            for c in chunks
        ],
        "_tokens": usage.to_dict(),
    }


@activity.defn
async def search_activity(query: str) -> dict[str, Any]:
    result = web_search(query)
    return {
        "query": result.query,
        "content": result.content,
        "source": result.source,
        "_tokens": result.tokens.to_dict(),
    }


@activity.defn
async def write_activity(query: str, search_results: list, chunks: list) -> dict[str, Any]:
    context_parts = []
    for c in chunks:
        context_parts.append(f"[{c.get('title', '')}] {c.get('content', '')}")
    for s in search_results:
        context_parts.append(f"[web:{s.get('query', '')}] {s.get('content', '')}")
    context = "\n\n".join(context_parts)
    system = (
        "You are a research writer. Produce a clear markdown report that answers the query "
        "using only the provided context. Start with a one-paragraph summary."
    )
    user = f"Query: {query}\n\nContext:\n{context}"
    text, usage = llm_call(system, user)
    return {"report": text, "_tokens": usage.to_dict()}


@activity.defn
async def evaluate_activity(query: str, report: str, context_chunks: list[str]) -> dict[str, Any]:
    result = evaluate_report(query, report, context_chunks)
    return {
        "faithfulness": result.faithfulness,
        "relevance": result.relevance,
        "overall": result.overall,
        "reasoning": result.reasoning,
        "passed": result.passed,
        "_tokens": result.tokens.to_dict(),
    }
