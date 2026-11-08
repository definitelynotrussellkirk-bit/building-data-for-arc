# Parametric sliding-window rule — proposed prototype

This task-local prototype preserves the original ARC family’s reasoning pattern:
scan every sliding square window, count those filled with one designated color,
and encode the count as a length-five unary bar. It adds two parameters chosen
**once per episode** and held fixed across all demonstrations and the query:

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `window_size` | `2`, `3` | `2` |
| `target_color` | `1`, `2` | `1` |

The default `(window_size=2, target_color=1)` returns the canonical Racket text
byte-for-byte. Variants still emit a `1 × 5` bar of color 1, so only the counted
window geometry and semantic target color change. The selected production
`generator.py`, canonical rule, approval hashes, and catalog state are untouched.

## Input constraints and teaching design

Each controlled 11 × 13 input has a zero background, one solid color-1 rectangle,
and one disjoint solid color-2 rectangle. Rectangle dimensions are selected so
the four parameter settings produce different label signatures. Seeded
orientation and placement vary the surface layout without changing those counts.
Every complete episode contains three labelled demonstrations and one query; all
three alternative settings are refuted by the demonstrations, and all four
settings also predict different outputs on the retained shared witness.

The four fixture signatures, ordered as `(2,1)`, `(2,2)`, `(3,1)`, `(3,2)`, are:

- demo 1: `2, 4, 0, 1`
- demo 2: `4, 3, 1, 0`
- demo 3: `3, 1, 0, 0`
- query: `4, 2, 1, 0`

Every label and rival output is produced by executing the exact instantiated rule
through the bundled Racket bridge. Python constructs inputs and evidence only; it
does not author labels.

## Run from the outer extracted packet directory

```sh
python3 review.py run python3 generators/2f7883fbd26f/workspace/parametric/prototype.py \
  --out ../checks/parametric/window-rule

python3 review.py run python3 -m pytest -q \
  generators/2f7883fbd26f/tests/test_parametric_window_rule.py
```

The materializer writes one complete private/public episode for each of the four
settings, exact `.rkt` files and hashes, runtime identity, source hashes, and a
shared differing witness. Public files include labelled demonstrations and masked
query inputs only; hidden parameters, programs, provenance, and query answers stay
under `private/`.

## Scope and limits

This is a runnable **proposed prototype**, not a production API or an approval.
Evidence covers two window sizes, two target colors, controlled rectangle
fixtures, four retained seeds, and the three declared parameter rivals. It does
not claim universal identifiability, arbitrary colors, arbitrary shapes, counts
above five, or integration into the selected canonical sampler.
