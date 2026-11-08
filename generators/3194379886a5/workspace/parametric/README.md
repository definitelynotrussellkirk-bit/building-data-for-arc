# 3194379886a5 parametric family

This task-local prototype preserves the canonical `matched_prototype` rule and adds `matched_color_pointer`.

- `matched_prototype`: match the query under the eight dihedral transforms and return that prototype in the query color.
- `matched_color_pointer`: match the query, read the matched panel's input color as a 1-based pointer, then return the pointed-to panel in the query color.

The same generated inputs are used for both settings. Episodes support 2–6 demonstrations and 1–4 distinct queries; native qualification uses two demonstrations and four queries.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -m pytest --import-mode=importlib -q \
  generators/3194379886a5/tests/test_generator_3194379886a5.py \
  generators/3194379886a5/workspace/parametric/tests/test_prototype.py

PYTHONPATH=shared/runtime python3 \
  generators/3194379886a5/workspace/parametric/audit.py \
  --out /tmp/3194379886a5-audit.json --seeds 32
```

`canonical.rkt` is byte-for-byte canonical. `matched_color_pointer.rkt` is the alternative program. The bounded audit checks the finite declared settings plus fixed-panel, projection-only, and cyclic-pointer rivals; it is not a universal identifiability proof.
