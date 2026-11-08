# Feedback to Codex

## F1: Biggest avoidable friction: missing manifest was reported as a missing prototype

Symptom: the first `9c69eb63c11a` qualification attempt failed with a generic prototype-missing/currentness error even though `adapter.py`, `promotion.json`, and `canonical.rkt` already existed. Evidence: qualification succeeded immediately after creating the required source/evidence manifest, without changing adapter behavior. Suggested change: make the qualifier name the absent/stale `workspace/parametric/evidence/manifest.json` and print the exact guarded `parametric manifest` command.

## F2: Direct pytest and staged task tests expose different repository layouts

Symptom: raw task-local pytest could not materialize the legacy `puzzle_generators.per_puzzle` namespace, while the official staged runner did; the staged runner then exposed a separate hard-coded `parents[1]` canonical-data path defect. Evidence: the repaired test uses `reviewer_support.find_root`/`canonical_pairs`, and the staged gate now passes 66/66. Suggested change: add a small standard portable-test helper/template and make raw-test guidance point to it before authors encode repository-depth assumptions.
