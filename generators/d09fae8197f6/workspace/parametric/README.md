# Orientation-scope parametric prototype

This task-local prototype leaves the production generator, canonical Racket
program, and `RULE_HASH` unchanged. It declares one bounded rule parameter,
selected once and held fixed across a complete episode:

| Parameter | Allowed values | Original/default |
|---|---|---|
| `orientation_scope` | `dihedral`, `rotations` | `dihedral` |

Both settings locate the yellow/magenta template, slide its orientations over
the dense field, require every in-bounds magenta marker to match and every body
cell to avoid magenta, and stamp yellow body cells on a match. `dihedral`
searches all eight rotations/reflections, exactly preserving the canonical rule.
`rotations` searches only the four rotations. The input grammar does not change.

The sampler uses lawful production-generator inputs and retains only cases where
both settings visibly stamp at least one cell and disagree. Thus every retained
demonstration identifies the chosen setting against the sole declared rival.
Sampling is bounded to 128 candidates per pair and fails loudly rather than
cloning inputs or silently returning fewer pairs.

Run the focused tests from the packet extraction root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d09fae8197f6/tests/test_parametric_orientation_scope.py \
  generators/d09fae8197f6/tests/test_parametric_public_names.py
```

Build exact two-setting evidence, with three demonstrations and four distinct
queries per episode, through the bundled Racket runtime:

```bash
python3 review.py run python3 \
  generators/d09fae8197f6/workspace/parametric/build_evidence.py \
  --out ../checks/parametric/orientation-scope-v1
```

Generate a single private or answer-masked four-query episode:

```bash
python3 review.py run python3 \
  generators/d09fae8197f6/workspace/parametric/prototype.py \
  --seed 17 --orientation-scope rotations --demo-count 3 --query-count 4 \
  --out ../checks/parametric/example-private.json

python3 review.py run python3 \
  generators/d09fae8197f6/workspace/parametric/prototype.py \
  --seed 17 --orientation-scope rotations --demo-count 3 --query-count 4 \
  --public --out ../checks/parametric/example-public.json
```

Public challenges omit the setting, program, source slots, private metadata and
query outputs. Their opaque filename is the SHA-256 of the exact visible
challenge bytes (demonstration inputs/outputs plus query inputs), so seeds,
settings and query answers cannot affect it.

The retained evidence is a proposed bounded extension only. It does not approve
the alternative setting, change the selected canonical authority, or admit any
trajectory to training.
