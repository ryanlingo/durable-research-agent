from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: TokenUsage) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class SearchResult:
    query: str
    content: str
    source: str = "web"
    tokens: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    content: str
    score: float


@dataclass
class EvaluationResult:
    faithfulness: float
    relevance: float
    overall: float
    reasoning: str
    tokens: TokenUsage = field(default_factory=TokenUsage)

    @property
    def passed(self) -> bool:
        return self.overall >= 0.7


@dataclass
class ResearchReport:
    query: str
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str] = field(default_factory=list)
    evaluation: EvaluationResult | None = None
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    steps: list[str] = field(default_factory=list)


@dataclass
class ClarificationRequest:
    questions: list[str]
    reason: str


@dataclass
class AgentState:
    """Minimal shared state shape used by the non-Temporal version."""

    query: str
    status: str = "started"
    clarification: ClarificationRequest | None = None
    clarified_query: str | None = None
    search_plan: list[str] = field(default_factory=list)
    search_results: list[SearchResult] = field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    draft_report: str | None = None
    evaluation: EvaluationResult | None = None
    final_report: ResearchReport | None = None
    approval_status: str = "pending"  # pending | approved | rejected
    total_tokens: TokenUsage = field(default_factory=TokenUsage)
    history: list[dict[str, Any]] = field(default_factory=list)

    def checkpoint(self) -> dict[str, Any]:
        search_results = [
            {
                "query": r.query,
                "content": r.content,
                "source": r.source,
                "tokens": r.tokens.to_dict() if isinstance(r.tokens, TokenUsage) else r.tokens,
            }
            for r in self.search_results
        ]
        evaluation = None
        if self.evaluation:
            evaluation = {
                "faithfulness": self.evaluation.faithfulness,
                "relevance": self.evaluation.relevance,
                "overall": self.evaluation.overall,
                "reasoning": self.evaluation.reasoning,
                "tokens": self.evaluation.tokens.to_dict()
                if isinstance(self.evaluation.tokens, TokenUsage)
                else self.evaluation.tokens,
            }
        return {
            "query": self.query,
            "status": self.status,
            "clarification": self.clarification.__dict__ if self.clarification else None,
            "clarified_query": self.clarified_query,
            "search_plan": self.search_plan,
            "search_results": search_results,
            "retrieved_chunks": [c.__dict__ for c in self.retrieved_chunks],
            "draft_report": self.draft_report,
            "evaluation": evaluation,
            "approval_status": self.approval_status,
            "total_tokens": self.total_tokens.to_dict(),
            "history": self.history,
        }
