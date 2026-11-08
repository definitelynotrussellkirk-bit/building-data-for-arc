# Row-front extent/source-policy parametric prototype

This task-local prototype leaves the approved `66e63986855b` generator and its
canonical Racket authority unchanged. It chooses two small rule parameters once
per deterministic episode and keeps them fixed across every demonstration and
query:

- `fill_extent = reflected` (**canonical/default**): fill from each interior
  row's frontier through the point reflected across the global rightmost source
  column.
- `fill_extent = to_axis` (**proposed**): fill only through that global
  rightmost column.
- `source_policy = clear` (**canonical/default**): clear the source outline
  before painting the fill.
- `source_policy = retain` (**proposed**): retain the source outline and add the
  same fill.

All four combinations are executable. The invariant reasoning is to identify the
occupied row span, global rightmost source column, each interior row's frontier,
and the source color, then paint a right-side interval. The parameters change
only the interval endpoint and initial canvas. Input constraints do not depend on
the setting.

## Files

- `prototype.py` builds 3-demonstration/4-query episodes, labels every retained
  pair and parameter rival with the included protected Racket runtime, checks an
  independent Python mirror, verifies every query from demonstrations alone,
  and writes private evidence plus answer-masked public challenges.
- `rules/*.rkt` contains the four exact materialized programs. The
  `reflected-clear.rkt` file is byte-identical to the canonical rule.
- `examples/` contains only public visible bytes. Filenames are SHA-256 IDs of
  visible demonstration inputs/outputs and query inputs, so no seed, setting,
  setting ordinal, reference code, metadata, or query answer is encoded. The
  writer sorts by public ID, rejects duplicate visible payloads, refuses
  overwrites, and rolls back the private install if the public install fails.

## Exact replay

From the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/66e63986855b/workspace/parametric/prototype.py \
  --out-dir ../checks/parametric/66e63986855b-row-front-v1 \
  --public-dir generators/66e63986855b/workspace/parametric/examples \
  --seeds 0 1 2 3 \
  --difficulty medium \
  --start-index 0 \
  --n-train 3 \
  --n-test 4
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/66e63986855b/tests/test_parametric_row_front.py
```

The retained evidence is bounded to seeds `0..3`, medium inputs drawn from the
selected generator, and the four declared settings. It is a **proposed,
unapproved prototype**. It does not alter production generation, canonical rule
hashes, generator approval, or training admission, and it does not claim to
cover every possible fill-extent or source-composition rival.
