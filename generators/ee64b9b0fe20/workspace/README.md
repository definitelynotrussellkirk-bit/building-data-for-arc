# Reusable review tools and next-agent handoff

The selected implementation is `../generator.py`. Everything here is authoring
support, never an automatically selected training generator.

## Final-source reproduction

From the extracted packet root, use fresh output names:

```sh
python3 review.py run python3 -m pytest -q generators/ee64b9b0fe20/tests
python3 review.py run python3 -m arcpuzzles check ee64b9b0fe20 \
  --battery --timeout 4000 --phase after --out ../checks/recheck-battery
python3 review.py run python3 -m arcpuzzles lesson-census ee64b9b0fe20 \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/recheck-lesson-census.json
python3 review.py run python3 generators/ee64b9b0fe20/workspace/final_shortcut_probe.py \
  --out ../checks/recheck-shortcut
python3 review.py run python3 -m arcpuzzles apply ee64b9b0fe20 \
  --input ../checks/recheck-shortcut/input.json \
  --out ../checks/recheck-shortcut/racket.json
python3 review.py run python3 generators/ee64b9b0fe20/workspace/final_shortcut_probe.py \
  --out ../checks/recheck-shortcut \
  --racket-receipt ../checks/recheck-shortcut/racket.json
python3 review.py run python3 generators/ee64b9b0fe20/workspace/parametric/sort_order_prototype.py \
  --out ../checks/recheck-parametric
```

The wrapper changes cwd to `WORK/repo`, configures the offline runtime and records
source-bound execution details. The repository's bare `pytest` does not discover
all task-local regressions, so invoke the task test directory explicitly.

## Tools

- `final_shortcut_probe.py` iterates the current `CANONICAL_SHORTCUTS`, verifies
  every labeled canonical pair, searches the current generator for an emitted
  disagreement input, and binds the result to a supplied Racket receipt.
- `parametric/sort_order_prototype.py` is a proposed-only extension. It chooses
  ascending or descending cell-count order once per episode, emits 3 demos + 1
  query, strips private answers from public challenges and executes both Racket
  programs in a copied runtime.
- `review_probe.py` and `diagnose_runtime_timeout.py` are retained from the prior
  review for historical reproduction. Their older census/source paths are not
  the decisive v3.1 evidence.

These tools read reference material and are forbidden during a closed-reference
solve. The final exposed solve is already frozen under `WORK/solve/` and correctly
declares earlier rule exposure.

## Final evidence

- Generator SHA-256:
  `f416fc7ff7204f8c8fce0862f1a0c56bc6c0dcae0c08dfb28db381ab7760bbd1`
- Battery: `checks/after-v2/checks/ee64b9b0fe20_after_battery_summary.json`
- Portable tests: `checks/task-tests/result.json`
- Lesson census: `checks/lesson-census-final.summary.json`
- Shortcut receipt: `checks/question-answer/fixed-background-7-final/probe.json`
- Parametric receipt: `checks/parametric/sort-order-final/summary.json`

Version 3.1 resolves the prior frame-coverage blocker by alternating default frame
presence by sample index and declaring an executable frame-preservation rival.
Finite named-rival evidence is not universal identifiability or training approval.
