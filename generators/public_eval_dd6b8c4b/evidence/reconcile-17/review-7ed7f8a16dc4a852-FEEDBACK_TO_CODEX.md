# Biggest avoidable friction: stage-specific first-turn validation

F1: `check_first_turn.py` hard-requires `exports/private/qualification.json`, so it crashes on valid public-authoring bundles before owner qualification. Accept the authoring preflight/presentation receipt for this stage, or return a clear “not applicable until qualification” result instead of `FileNotFoundError`.
