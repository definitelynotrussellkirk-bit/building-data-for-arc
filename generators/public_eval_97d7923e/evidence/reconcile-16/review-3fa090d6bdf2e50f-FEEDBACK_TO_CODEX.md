# Biggest avoidable friction: public-creation causal witness assembly

F1: Public-creation preflight has no witness-template/build command, so reviewers must manually copy the source binding and know that `witness.racket` must be the minimal protected-Racket claim rather than the evaluator's full runtime identity. Add a `review_public_creation witness build/check` helper that selects an exact preflight pair, emits the package-compatible schema, and fresh-replays both programs.
