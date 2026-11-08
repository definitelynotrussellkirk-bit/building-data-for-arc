# Task-local review tools — 82b2be9b4f4e

The selected implementation is `../generator.py`. These scripts are review and
qualification tools, not alternate generators or label authorities.

## Cyclic lesson-rotation probe

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -B \
  generators/82b2be9b4f4e/workspace/lesson_rotation_probe.py \
  --seeds 100 --period 4 --out /tmp/82b2be9b4f4e-rotations.json
```

The probe uses an independent Python connected-components/crop/upscale oracle.
It loads every rival actually declared in `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS`, verifies that each rival fits all canonical pairs, then
checks all four choices of query within every four-consecutive-pair window.
Every remaining three-demo set must refute every rival. It also checks
self-validation, strict validation, determinism, schedule profiles, unique
inputs, and that at least one two-object discriminator remains after every
query rotation. It does **not** execute Racket; use the repository battery and
lesson census for authority-bound parity.

The default 100 seeds × 4 starts × 4 rotations × 3 bands covers 4,800 rotated
lessons (1,200 windows; 4,800 generated pair positions before repeated-window
reuse). Use a new output path for each run so earlier failures remain retained.
