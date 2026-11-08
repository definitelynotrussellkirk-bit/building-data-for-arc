# 3ffc7ef20035 orientation-selector parameter family

This task-local family preserves the exact canonical `all_blue_bbox` program.
Its alternative, `bar_orientation_component`, reads the non-blue selector bar:
horizontal selects the first row-major blue object and vertical selects the
second; it then fills that selected object's tight bounding box cyan.

The two settings use identical input sampling for the same seed/count request.
Every episode has two separate sparse blue objects and one separate 2–3 cell
selector bar. The first two demonstrations use the same selector color and
length but opposite orientations, so color-, length-, fixed-index-, size-,
horizontal-position-, and proximity-only shortcuts do not explain both labels.

Native qualification command from the packet root:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 3ffc7ef20035 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/3ffc7ef20035/qualification --summary
```

The fourth query is a substantive 30×30 case with 24- and 27-cell sparse blue
objects spread across a 26×24 global blue bounding box. Public projection is one
query at a time through `prototype.public_turn`; settings, programs, query
answers, future inputs, seeds, and total-query hints stay private.
