# Workspace tools

`reference_probe.py` is the independent review oracle for task `f7a512650552`. It deliberately does not import transformation helpers from `generator.py`, so task-local tests can detect mirrored production bugs rather than merely repeat them.

Useful entry points:

- `load_generator(path=None)` — load a selected generator file without package-name assumptions.
- `canonical_pairs()` — read the portable labeled canonical pairs through `reviewer_support`.
- `parse(grid)` / `observed(grid)` — validate the three-panel structure and recover every advertised exact axis from pixels.
- `rule_output(grid)` — independent Python mirror of the pinned Racket semantics.
- `always_row_output`, `always_column_output`, `copy_query_output`, `solid_bbox_output` — concrete semantic rivals.
- `palette_size(grid)` — small profile helper used by the canonical-anchor tests.

Example from the packet's `repo/` directory:

```bash
PYTHONPATH=src:. python3 - <<'PY'
from generators.f7a512650552.workspace.reference_probe import load_generator, observed, rule_output

gen = load_generator()
grid = gen.generate(17, 9, difficulty="hard", mode=1)
print(observed(grid))
print(rule_output(grid))
PY
```

The selected implementation remains `../generator.py`; workspace files are never automatically selected for generation.
