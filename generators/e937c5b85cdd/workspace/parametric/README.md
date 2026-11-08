# Projection-polarity parametric prototype

This isolated prototype leaves the selected `generate()` path, canonical Racket
authority, `RULE_HASH`, and approval identity untouched. It adds one episode-level
parameter:

- `opposite` (original): clear the frame cell faced by each longest arm and paint
  the opposite frame cell with the cross color.
- `facing` (alternative): clear the opposite frame cell and paint the faced frame
  cell with the cross color.

The parameter is selected exactly once per episode. Inputs retain the production
generator's collision-free framed-cross grammar. Three demonstrations and one
query are generated under one setting; every label and rival prediction is
obtained by applying an exact, materialized Racket program through the protected
Racket bridge. Public files omit the parameter, program, seed, and query output.

From the packet root, create fresh evidence with:

```bash
python3 review.py run python3 \
  generators/e937c5b85cdd/workspace/parametric/prototype.py \
  --out ../checks/parametric/projection-polarity-v1
```

Run the focused regression tests with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/e937c5b85cdd/tests/test_input_contract.py \
  generators/e937c5b85cdd/tests/test_parametric_projection_polarity.py
```

The output directory contains two complete private episodes, matching public
challenges, both exact Racket programs, a direct differing witness, a report, and
a SHA-256 manifest. It is proposal evidence, not production approval.
