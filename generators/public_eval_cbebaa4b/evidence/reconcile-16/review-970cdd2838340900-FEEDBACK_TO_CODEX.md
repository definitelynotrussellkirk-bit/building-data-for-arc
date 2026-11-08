# Biggest avoidable friction: public preflights cannot use the standard witness helper

F1: `arcpuzzles.review_witness` accepts only native qualification receipts even though public-creation preflights carry the same source binding, program map, and audited execution needed for a standard causal witness. Extending that helper with a validated public-preflight mode would eliminate task-specific witness assembly and reduce the chance of schema or source-binding mistakes.
