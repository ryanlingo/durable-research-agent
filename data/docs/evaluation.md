# Evaluating agent outputs

LLM-as-judge is a practical evaluation method for research agents. Dimensions used in this lab:

- Faithfulness: is every factual claim supported by retrieved context?
- Relevance: does the report answer the original query?
- Overall: average of faithfulness and relevance. Pass threshold: 0.7.

A score below threshold should trigger refinement rather than silent acceptance. Evaluation is a first-class control-flow step (an Activity on the Temporal path) that can fail, cost tokens, and interact with crash recovery independently of generation. Human approval comes after the machine gate so reviewers are not the first filter for ungrounded drafts.
