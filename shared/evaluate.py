"""LLM-as-judge evaluation for research reports."""

from __future__ import annotations

import json

from openai import OpenAI

from .config import LLM_MODEL, model_supports_temperature
from .types import EvaluationResult, TokenUsage

EVAL_PROMPT = """You are a strict evaluator of research reports.

Query: {query}

Retrieved context:
{context}

Report:
{report}

Score the report on two dimensions from 0.0 to 1.0:
1. faithfulness - every factual claim is supported by the retrieved context
2. relevance - the report directly answers the query

Return ONLY valid JSON:
{{
  "faithfulness": <float>,
  "relevance": <float>,
  "overall": <float>,  // average of the two
  "reasoning": "<one short paragraph>"
}}
"""


def evaluate_report(
    query: str,
    report: str,
    context_chunks: list[str],
    model: str | None = None,
) -> EvaluationResult:
    client = OpenAI()
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no context)"
    prompt = EVAL_PROMPT.format(query=query, context=context, report=report)

    chosen = model or LLM_MODEL
    kwargs: dict = {
        "model": chosen,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    if model_supports_temperature(chosen):
        kwargs["temperature"] = 0.0
    resp = client.chat.completions.create(**kwargs)

    usage = TokenUsage()
    if resp.usage:
        usage.prompt_tokens = resp.usage.prompt_tokens
        usage.completion_tokens = resp.usage.completion_tokens
        usage.total_tokens = resp.usage.total_tokens

    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "faithfulness": 0.5,
            "relevance": 0.5,
            "overall": 0.5,
            "reasoning": "Failed to parse judge response",
        }

    return EvaluationResult(
        faithfulness=float(data.get("faithfulness", 0.5)),
        relevance=float(data.get("relevance", 0.5)),
        overall=float(data.get("overall", 0.5)),
        reasoning=str(data.get("reasoning", "")),
        tokens=usage,
    )
