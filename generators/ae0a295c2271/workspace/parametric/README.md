# Proposed `shape_equivalence` parameter

This task-local prototype keeps the canonical object-frequency reasoning and
varies only the equivalence relation used to form shape classes:

- `exact` — canonical/default; translation-normalized shapes must be identical.
- `d4` — proposed; rotations and reflections belong to the same class.

The setting is chosen once per complete episode. Each episode has three visible
demonstrations and one query. All four inputs contain two repeated exact classes
and two exact singleton classes from one D4 orbit, so every demonstration
separates the two settings. Labels are executed by the bundled Racket runtime;
the Python implementation is parity-only.

From the outer packet directory:

```bash
python3 review.py run python3 generators/ae0a295c2271/workspace/parametric/prototype.py \
  materialize --out ../checks/parametric/ae0a295c2271-shape-equivalence
python3 review.py run python3 generators/ae0a295c2271/workspace/parametric/prototype.py \
  verify --out ../checks/parametric/ae0a295c2271-shape-equivalence
python3 review.py run python3 -m pytest -q \
  generators/ae0a295c2271/tests/test_parametric_shape_equivalence.py
```

This is a proposed prototype, not a production integration or authority change.
`exact` remains the only selected canonical rule.
