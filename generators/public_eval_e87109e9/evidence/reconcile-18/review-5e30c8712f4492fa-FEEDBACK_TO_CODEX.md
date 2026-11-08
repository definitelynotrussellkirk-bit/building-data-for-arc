# Feedback to Codex

F1: Biggest avoidable friction: public-creation preflight has no first-class sequential public-projection/privacy gate.
Each task required a nearly identical source-bound audit for one-query views, hidden future queries, private settings/programs/answers, and first-turn invariance. Add a reusable `review_public_creation projection-audit` command that consumes `preflight.json` and an adapter, emits the standard receipt, and tests total-query-count independence plus private-field mutations.
