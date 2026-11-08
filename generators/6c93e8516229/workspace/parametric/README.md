# Proposed `junction_degree` rule parameter

This task-local prototype preserves the original topology-classification flow:
find each 4-connected green component, inspect local cell degrees and turns,
then recolor the entire component. One hidden episode-level parameter varies:

- `junction_degree ∈ {3, 4}`
- canonical/default: `3`
- `3`: a component containing a degree-3 cell is red (`2`)
- `4`: a component containing a degree-4 cell is red (`2`)
- in both settings, absent the selected junction, exactly two orthogonal turns
  are magenta (`6`), and every other component is blue (`1`)

Every retained demonstration contains both a degree-3 T and a degree-4 plus, so
the two settings predict different visible labels. The setting is selected once
from the episode seed and reused for all three demonstrations and the query.
Public challenge files contain only demonstration inputs/outputs and query
inputs; private evidence retains the parameter, exact Racket, query answer,
hashes, and rival checks.

From the outer packet directory, materialize Racket-backed evidence with:

```sh
python3 review.py run python3 generators/6c93e8516229/workspace/parametric/prototype.py \
  --out ../checks/parametric/junction-degree --seeds 0 1
```

Run the focused contracts with:

```sh
python3 review.py run python3 -m pytest -q \
  generators/6c93e8516229/tests/test_parametric_junction_degree.py
```

This is a proposed prototype only. It does not change the selected canonical
Racket authority, `RULE_HASH`, production `generate(...)`, or approval state.
