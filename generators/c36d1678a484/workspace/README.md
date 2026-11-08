# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Retained baseline

- `generator-v2.0.1.py` — immutable imported generator used for the before battery and red regression run.

## Reusable probes

The task-local regression harness is `../tests/test_generator.py`. It uses the portable `reviewer_support.find_root()` and `canonical_pairs()` helpers, accepts `GENERATOR_UNDER_TEST` for replaying alternate drafts, and tests:

- canonical input acceptance and independent Python-rule parity;
- exact/rejecting override behavior;
- presence of all three semantic counterexamples in every sampled grid;
- exact canonical-profile support under the battery's pinned schedule;
- rival disagreement and query-rotation identifiability.

From packet root:

```bash
python3 run_with_racket.py python3 -m pytest -q generators/c36d1678a484/tests
python3 run_with_racket.py python3 -m arcpuzzles check c36d1678a484 --battery --timeout 4000 --phase after --out ../checks/after
python3 run_with_racket.py python3 -m arcpuzzles lesson-census c36d1678a484 --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json
```
