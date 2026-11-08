# Workspace

`probe_curriculum.py` is a portable, source-bound reviewer probe for this task.
It reads the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`,
`SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` declarations rather than maintaining a
second rival list.

It exhausts all eight cyclic schedule starts for supplied seeds and difficulty
bands, holds out every query position in each four-pair window, verifies witness
claims, and checks the complete advertised canvas/opening/depth/lateral geometry
cross-product for observable-coordinate collisions.

Example from the repository root:

```bash
python3 generators/c5a69e7cd8c8/workspace/probe_curriculum.py \
  --seeds 12317 12319 12323 12329 12343 \
  --starts 8 \
  --out ../checks/curriculum-probe.json
```

The probe uses the task's independent Python rule mirror for generated labels.
Use the shared semantic gate and `lesson-census --rotate-query` for authoritative
Racket-labelled evidence. Passing this finite declared-rival probe does not rule
out undeclared shortcuts.
