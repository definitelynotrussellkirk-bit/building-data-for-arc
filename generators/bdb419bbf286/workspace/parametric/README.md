# bdb419bbf286 parametric family

This task-local prototype preserves the canonical `fixed_three` rule and adds `to_boundary`.

- `fixed_three`: select the first color-2 object and first row-major 3/4 marker pair, then paint copies at `k = 0, 1, 2`.
- `to_boundary`: derive the same input-specific shape/vector intermediate, then keep translating until no later copy has an in-bounds cell.

Every generated scene has later 3/4 decoys whose last-marker vector produces a different output. The same generated inputs are used for both settings. Episodes support 2–6 demonstrations and 1–4 distinct queries; native qualification uses two demonstrations and four queries.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -m pytest --import-mode=importlib -q \
  generators/bdb419bbf286/tests/test_generator_bdb419bbf286.py \
  generators/bdb419bbf286/workspace/parametric/tests/test_prototype.py

PYTHONPATH=shared/runtime python3 \
  generators/bdb419bbf286/workspace/parametric/audit.py \
  --out /tmp/bdb419bbf286-audit.json --seeds 32
```

`canonical.rkt` is byte-for-byte canonical. `to_boundary.rkt` is the alternative program. The bounded audit checks the finite declared settings, fixed repeat counts 1/2/4/5/6, and last-marker variants; it is not a universal identifiability proof. The catalog's historical semantic veto is intentionally not edited here: owner source review must clear it before native qualification and acceptance.
