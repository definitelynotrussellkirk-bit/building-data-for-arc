# Workspace tools for a5e17b975ae0

The selected implementation is `../generator.py`. Workspace files are source-bound probes or review helpers and are never automatically selected as the generator.

## `reference_probe.py`

Independent canonical/profile inspection used to derive the repair contract. It reads the public canonical ledger, reports size/palette profiles, and applies an independent flood oracle. It is not used by production generation.

## `cyclic_lesson_probe.py`

Exhaustively checks the deterministic five-slot curriculum rather than sampling only ordinary production windows. It imports and hashes the exact generator bytes, iterates the generator's own `LESSON_COMPETITORS`, and checks all cyclic starts and all four possible query rotations for each lesson.

From the packet root:

```bash
python3 repo/generators/a5e17b975ae0/workspace/cyclic_lesson_probe.py \
  --seeds 25 \
  --out checks/cyclic-lesson-probe.json
```

The retained final run covered 500 lesson windows and 2,000 query rotations with zero declared-rival ambiguities. This is a finite source-bound check, not a proof of universal identifiability; Racket parity remains the responsibility of the battery's `rule_smoke` stage.
