# Review workspace for 3bb94038f4e2

The selected implementation is `../generator.py`. These tools are review/test support and never supply training labels.

## `reference_probe.py`

Provides an independent Python oracle, canonical-pair/profile helpers, semantic-feature extraction, and optional real-Racket parity. The Python mirror is diagnostic only; the selected canonical Racket program remains label authority.

## `analyze_curriculum.py`

Runs a source-bound deterministic audit of ordinary draws plus every held-out query position for consecutive four-pair schedule windows. It reads rival/witness declarations from the generator rather than duplicating their names.

From the packet root:

```sh
env RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket" \
  PYTHONPATH=repo/shared/runtime \
  python3 repo/generators/3bb94038f4e2/workspace/analyze_curriculum.py \
  --per-band 100 --cyclic-starts 24 \
  --out checks/task-curriculum-audit.json
```

The final retained run is `checks/task-curriculum-audit-final2.json`: 300 draws, 288 rotations, zero semantic or determinism failures.

## Production lesson census

The task-local analyzer deliberately complements rather than replaces the real lesson materializer. The production check must also be run because it performs duplicate rejection and may consume later sample indices:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 3bb94038f4e2 \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census.json
```

The pre-fix census in `checks/lesson-census-final.json` retains three duplicate-induced ambiguous rotations. The final census in `checks/lesson-census-final2.json` reports zero ambiguities across 300 lessons and 1,200 query rotations.
