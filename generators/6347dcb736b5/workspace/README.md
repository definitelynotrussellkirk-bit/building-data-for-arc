# Workspace for 6347dcb736b5

The selected implementation is `../generator.py`. Workspace code is diagnostic
and is never selected automatically.

## `reference_probe.py`

An independent geometry oracle that deliberately does **not** import the selected
generator. It exposes:

- `objects(grid)` — same-color 4-connected components and bboxes;
- `oracle(grid)` — per-component bbox outlines on a fresh canvas;
- `fill_bbox(grid)` — full-bbox rival;
- `outline_over_input(grid)` — non-erasing overlay rival;
- `global_color_bbox(grid)` — canonical-fitting color-grouping rival;
- `facts(grid)` and `profile_signature(grid)` — reusable distribution probes.

Example from the packet root:

```bash
PYTHONPATH=repo/generators/6347dcb736b5/workspace python3 - <<'PY'
from reference_probe import facts, oracle, global_color_bbox

grid = [
    [1, 1, 0, 0, 1],
    [1, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
]
print(facts(grid))
print(oracle(grid) == global_color_bbox(grid))
PY
```

Use the selected Racket authority for decisive labels. This probe is for
cross-checks, rival construction, and task-local tests.
