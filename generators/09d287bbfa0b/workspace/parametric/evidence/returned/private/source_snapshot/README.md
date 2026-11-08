# Proposed `scan_order` rule parameter

Status: **proposed task-local prototype**, not canonical approval and not a
production generator API.

The canonical/default setting is `row_major`. The alternative
`reverse_row_major` preserves the same background, cross detection, source
eligibility, reflection orbit, clipping, and overwrite operation; it changes
only the order in which original off-axis source cells are traversed. The exact
canonical Racket bytes are returned unchanged for the default. The alternative
is materialized by one pinned source-fragment substitution and both programs
are executed through `RacketBridge`.

Each episode selects one setting once from its deterministic seed and keeps it
fixed for all three demonstrations and the query. Inputs are produced by the
selected generator with `texture="multi_quadrant"` and `n_pixels=8`. Those
constraints are the same for both settings and force a fully visible,
distinct-color same-orbit collision, so every retained demonstration and query
distinguishes the two traversal orders. Public files contain only labelled
training pairs and an unlabelled query; parameter values, rule source, rival
predictions, and query answers stay under `private/`.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/09d287bbfa0b/workspace/parametric/prototype.py \
  --seeds 0 1 --difficulty medium --start 0 \
  --out ../checks/parametric/final
```

Focused tests:

```bash
python3 review.py run pytest -q \
  generators/09d287bbfa0b/tests/test_parametric_scan_order.py
```

The evidence is bounded to the requested seeds, difficulty, start, and declared
parameter rival. It does not prove identifiability against every conceivable ARC
rule, and acceptance of the canonical generator does not approve this variant.
