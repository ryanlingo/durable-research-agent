# Evaluating Agent Outputs

LLM-as-judge is a practical evaluation method for research agents. Typical dimensions:
- Faithfulness: does every claim appear in the source material?
- Relevance: does the answer address the original query?
- Completeness: are important aspects missing?

A score below threshold should trigger refinement rather than silent acceptance. Evaluation itself should be treated as a first-class step that can fail and be retried independently of generation.
