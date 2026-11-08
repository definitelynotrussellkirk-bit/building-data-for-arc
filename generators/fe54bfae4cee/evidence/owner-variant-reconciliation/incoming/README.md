# Midpoint fill-pass family for fe54bfae4cee

This native family varies one episode-fixed parameter:

- `fill_passes=1` (default) is the exact canonical Racket source, byte for byte.
- `fill_passes=2` runs the same complete midpoint rule on the first pass's
  output, allowing newly created endpoints to enable one additional fill.

The sampler uses matched inputs across settings. Every lesson begins with a
relay chain where pass one creates the endpoint consumed by pass two. The second
demonstration includes a three-stage relay, separating exactly two passes from
an until-stable shortcut. Lessons also include longer-span, diagonal, blocked,
standalone, and crossed-pair controls. The crossed pair teaches the canonical
horizontal-then-vertical last-write behavior without changing the production
generator's narrower domain.

Episodes support 2–6 demonstrations and exactly four distinct queries. Query
shapes are 7×7, 12×12, 18×24, and a substantive 30×30 tiled stress case.
Protected-Racket qualification is the label authority; Python mirrors are
sampler checks and bounded adversarial evidence.

From the repository root, reproduce the finite demonstration-only audit with:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/fe54bfae4cee/workspace/parametric/self_audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --demos 6 --queries 4
```

The audit covers only its declared rivals and does not claim universal rule
uniqueness.
