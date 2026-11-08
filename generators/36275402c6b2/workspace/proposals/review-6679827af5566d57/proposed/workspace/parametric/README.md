# Proposed `border_policy` rule parameter

This task-local prototype preserves the original reasoning pipeline: find the
unique largest same-color component, crop its bounding box, read every isolated
outside horizontal pair as `(replacement, source)`, and apply the resulting
mapping to the crop. One hidden episode-level parameter varies:

- `border_policy ∈ {recolor, preserve}`
- canonical/default: `recolor`
- `recolor`: replace source colors everywhere in the crop, including its border
- `preserve`: replace source colors only in the crop interior

Every retained demonstration and query uses the canonical generator's
`border_and_side` profile and therefore contains a non-corner source cell on the
crop border. The two settings predict different visible outputs on every example.
The setting is selected once from the episode seed and reused for all three
demonstrations and the query. Public challenge files contain only demonstration
inputs/outputs and query inputs; private evidence retains the parameter, exact
Racket, query answer, hashes, and rival checks.

From the outer packet directory, materialize Racket-backed evidence with:

```sh
python3 review.py run python3 generators/36275402c6b2/workspace/parametric/prototype.py \
  --out ../checks/parametric/border-policy --seeds 0 1
```

Run the focused contracts with:

```sh
python3 review.py run python3 -m pytest -q \
  generators/36275402c6b2/tests/test_parametric_border_policy.py
```

This is a proposed prototype only. It does not change the selected canonical
Racket authority, `RULE_HASH`, production `generate(...)`, or approval state.
