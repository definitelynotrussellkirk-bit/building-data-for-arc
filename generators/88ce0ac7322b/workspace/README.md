# Workspace

The selected implementation is `../generator.py`; files here are retained review
probes and are never automatically selected as generator code.

## `rival_probe.py`

A source-bound regression probe for future edits. It dynamically reads the
selected generator's `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies
that declared shortcuts fit all labeled canonical pairs, exhausts all 36 legal
profile/order/difficulty combinations, and checks every query rotation at all
15 cyclic schedule starts in each band using an independent Python rule mirror.
The repository battery remains the Racket authority check.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/88ce0ac7322b/workspace/rival_probe.py \
  --starts-per-band 15 \
  --out ../checks/rival-probe.json
```
