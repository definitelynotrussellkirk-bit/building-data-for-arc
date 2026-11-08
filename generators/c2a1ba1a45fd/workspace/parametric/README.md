# Native object-order family for `c2a1ba1a45fd`

Status: reviewer-ready prototype only after the retained checks pass. Owner integration, fresh qualification, exact-source acceptance, and any training admission remain separate.

## Episode-fixed parameter

`object_order` has two values over the same input grammar:

- `row_major` — the exact canonical Racket program, byte-for-byte. Row-major legend dots recolor row-major external source objects.
- `size_ascending` — preserve source-color inference, legend parsing, 8-connectivity, and painting, but order the same source objects by ascending cell count before pairing them with the row-major dots. Top-left breaks hypothetical size ties.

Inputs are identical across settings for the same seed and requested counts. Demonstrations and queries are independent prefixes; 2–6 demonstrations and 1–4 queries are supported.

## Required causal dependency

- **A:** infer the outside-frequency source color, extract its external 8-connected objects, compute each exact cell set, top-left position, and size, then order those objects under the episode setting.
- **Intermediate:** the setting-specific ordered list of four input-derived source-object cell sets.
- **B:** pair the four row-major legend colors with that ordered list and recolor each selected object.

B cannot choose which spatial cell set receives each legend color until A has parsed and ranked the source objects. The retained wrong-order witness keeps the input and legend fixed but substitutes the canonical row-major intermediate for the qualified `size_ascending` intermediate; protected Racket execution changes the final output.

## Constructive lesson grammar

Every scene contains four uniquely sized source objects whose row-major size sequence is deliberately non-monotone. One object is formed from two blocks touching only diagonally, so 8-connectivity matters. A source-colored cell inside the gray legend is deliberately earlier than the real dots and must be ignored. Two outside distractor components make source-frequency selection visible. Four queries cover `20x24`, `24x27`, `28x30`, and a substantive `30x30` scene with at least 120 source cells and canvas-boundary contact.

The minimum two-example lesson distinguishes both declared settings and a finite set of plausible shortcuts: descending size, reversed row-major order, column-major legend reading, 4-connected object parsing, treating the source-colored legend cell as a dot, and painting every object with the first dot color. This is bounded evidence, not universal semantic uniqueness.

## Files

- `adapter.py` — native adapter entry point.
- `family.py` — exact programs, constructive sampler, Python mirror, finite-rival audit, and public projection.
- `promotion.json` — native promotion contract.
- `evidence/manifest.json` — generated source/evidence inventory.

## Verification

From the packet outer directory:

```sh
python3 review.py run python3 -m pytest \
  generators/c2a1ba1a45fd/tests/test_parametric_object_order.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify c2a1ba1a45fd \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/c2a1ba1a45fd/qualification --summary
```
