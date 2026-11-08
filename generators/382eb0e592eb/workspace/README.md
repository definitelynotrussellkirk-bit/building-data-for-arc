# Reviewer workspace

The selected implementation is `../generator.py`; files here are source-bound reviewer tools or explicitly separate prototypes and are never selected automatically.

## `qualify.py`

A low-cost future-review gate that reads the selected generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` registries. It verifies every declared shortcut against every labeled canonical pair, then exhausts all four cyclic schedule starts and all four query rotations for easy, medium, and hard at a fixed seed (12 windows, 48 rotations).

```bash
python3 review.py run python3 generators/382eb0e592eb/workspace/qualify.py \
  --seed 0 --out ../checks/qualification/final.json
```

Its limits are deliberate: one seed and declared rivals only. The shared Racket battery and 100-per-band lesson census remain required.

## `parametric/`

A proposal-only vertical-direction family. Its default `down` materialization is the exact selected rule; the `up` variant and all private/public prototype episode evidence remain separate from canonical execution. See `parametric/README.md`.
