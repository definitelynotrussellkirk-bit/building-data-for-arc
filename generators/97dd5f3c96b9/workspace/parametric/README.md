# Proposed connector-color prototype

**Status:** task-local, proposed, and not production-approved. The selected
`generator.py`, canonical rule, `RULE_HASH`, approval state, and training
admission are unchanged.

This prototype keeps the original reasoning structure: find each color's two
aligned markers and connect them. One hidden `connector_color` setting is fixed
for the whole episode:

- `pair_color` — the exact canonical Racket source; each segment uses its marker color;
- `fixed_8` — preserve endpoints and paint only connector interiors color 8;
- `fixed_9` — preserve endpoints and paint only connector interiors color 9.

All settings share the production generator's lawful input grammar. Every input
contains three distinct marker colors, mixed orientations, nonempty interiors,
and disjoint inclusive spans, so one demonstration distinguishes the three
finite declared settings. Demo and query counts are independent exact integers
from 1 through 16; ordinary promotion evidence uses two demonstrations and four
distinct queries.

## Reproduce focused checks

From the extracted packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/97dd5f3c96b9/tests/test_parametric_connector_color.py
```

## Materialize protected-Racket evidence

Use a new destination (existing destinations are deliberately refused):

```bash
python3 review.py run python3 \
  generators/97dd5f3c96b9/workspace/parametric/prototype.py \
  --out ../checks/parametric/connector-color-replay \
  --seed 0 --seed 1 --seed 2 --demos 2 --queries 4
```

The writer emits:

- `public/challenge-<visible-bytes-sha256>.json` with demonstrations and query inputs only;
- `private/` receipts with hidden settings, query answers, exact programs, finite-rival checks, and protected-Racket runtime identity;
- `rules/` with the exact materialized Racket source for every setting;
- `manifest.json` binding hashes and limitations.

`adapter.py` plus `promotion.json` are promotion-ready inputs, not an acceptance
record. Owner qualification and explicit acceptance remain separate steps.
