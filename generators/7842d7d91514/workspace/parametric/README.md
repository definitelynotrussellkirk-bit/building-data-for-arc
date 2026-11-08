# Parametric family: 7842d7d91514

This task-local proposal preserves the accepted canonical setting exactly and
adds one nearby sequential setting.

- `exact`: compare candidates with the color-5 template without rotation.
- `selector_rotation`: count the connected color-8 selector, derive one
  intermediate (`2 -> one clockwise turn`, `4 -> one counterclockwise turn`),
  rotate the normalized template, then compare color-2 candidates with that
  derived target.

The input sampler is independent of the hidden setting. Two demonstrations are
the minimum: the first contains a 2-cell selector and the second a 4-cell
selector. Each scene contains all four rotations of a chiral template, both
output branches, same-size distractors, and isolated objects. Four fixed query
inputs include a 30x30, 20-candidate stress transfer.

Run focused checks from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/7842d7d91514/tests/test_parametric_family.py -q
```

Run the protected-Racket audit:

```bash
python3 review.py run python3 \
  generators/7842d7d91514/workspace/parametric/audit.py \
  --out generators/7842d7d91514/workspace/parametric/evidence/current/audit.json
```

This is a proposed, source-bound family. It is not owner-accepted and is not
admitted to training merely because local tests or qualification pass.
