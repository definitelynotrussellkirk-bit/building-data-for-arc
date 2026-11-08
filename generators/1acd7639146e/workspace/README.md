# Workspace

The selected implementation is `../generator.py`; workspace files are authoring aids and are never label authorities.

## `probe_schedule.py`

Enumerates every declared cyclic start and every single-pair query holdout for one or more seeds/bands. It independently renders the rectangle outline, then checks that every declared lesson competitor is refuted by at least one remaining demonstration.

Example from the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 generators/1acd7639146e/workspace/probe_schedule.py \
  --seed-count 32 --out var/review/schedule-probe-32.json
```

The probe exits nonzero on any unrefuted rival. Its report explicitly states that it is a Python diagnostic; use `arcpuzzles lesson-census` for Racket-bound evidence.
