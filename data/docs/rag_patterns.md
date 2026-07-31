# RAG Patterns for Agents

Retrieval-Augmented Generation improves factual grounding. Common production issues:
- Retrieval results must be checkpointed; re-running embeddings is wasteful
- Large context windows still benefit from selective retrieval
- Evaluation of faithfulness (is the answer supported by retrieved chunks?) is essential
- Hybrid search (keyword + dense) often outperforms pure vector search on technical corpora

When an agent crashes after retrieval but before generation, a durable system should resume with the already-retrieved chunks.
