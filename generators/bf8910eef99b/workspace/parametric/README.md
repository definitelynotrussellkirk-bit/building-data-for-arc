# Proposed `stamp_size` episode parameter

This isolated prototype preserves the original four-color 2x2 source block,
source-cell roles, diagonal-opposite target mapping, source preservation, and
natural grid clipping.  The hidden `stamp_size` is chosen once for an entire
three-demonstration/one-query episode:

- `2` — canonical/default behavior: emit 2x2 opposite-quadrant stamps.
- `1` — proposed nearby behavior: emit one nearest cell in each corresponding
  opposite quadrant.

The prototype is **proposed**, not selected or approved.  It is not imported by
the production generator.  Every retained label and rival prediction is
executed from the exact materialized Racket program.  Public episodes omit the
hidden value, Racket text, seed, and masked query answer.

From the extracted packet root:

```bash
python3 review.py run python3 generators/bf8910eef99b/workspace/parametric/stamp_size.py \
  evidence --seed 900 --out ../checks/parametric/stamp-size-900

python3 review.py run python3 -m pytest -q \
  generators/bf8910eef99b/tests/test_parametric_stamp_size.py
```

A single episode can also be materialized privately:

```bash
python3 review.py run python3 generators/bf8910eef99b/workspace/parametric/stamp_size.py \
  episode --seed 901 --stamp-size 1 \
  --out ../checks/parametric/stamp-size-episode-901.json
```

Limits: only sizes 1 and 2 are assessed; the two retained episodes establish
finite executable separation, not unique induction over all possible rival
rules; and no production, canonical, catalog, or approval metadata is changed.
