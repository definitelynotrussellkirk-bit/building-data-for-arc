# 48732ebd41f9 — unique greatest-area zero rectangle

## Rule

Find every solid axis-aligned rectangle of color `0` whose height is at least
2. Select the **unique rectangle with greatest area** and recolor its cells to
`6`; preserve every other cell. The selected Racket helper is historically
named `tallest-rect`, but its comparison key is area.

`RULE_HASH = 9d5297512997`

## Final generator distribution

The generator constructs one unique maximum-area target in a `2..10` by
`14..30` grid. A four-slot deterministic schedule gives every four-example
lesson:

1. `canonical_core`: target plus a wider-but-smaller and a taller-but-smaller
   zero rectangle;
2. `interior_rivals`: an interior target;
3. `edge_rivals`: a two-row edge target;
4. `accent_rivals`: a three-color input palette.

The schedule reproduces all four canonical public profiles
`(height, width, palette-size)`:

- `(2, 20, 2)`
- `(3, 30, 3)`
- `(4, 20, 2)`
- `(4, 24, 2)`

Rule-irrelevant foreground colors vary over every legal nonzero color other
than `6`, with canonical color `1` weighted more heavily. Additional isolated
zero noise cannot create another height-at-least-two rectangle. The generator
advertises exact observable controls for canvas size, foreground identity,
target size, target edge/interior placement, and binary/accent palette mode.
Impossible exact tuples raise a structured incompatibility instead of clipping
caller pins.

## Semantic contract

The retained Python mirror independently enumerates the same row-band zero
rectangles as the selected Racket program. Declared rivals are:

- `full_height_only`
- `widest_only`
- `tallest_only`

Declared witnesses ensure that each rival disagrees with the intended rule in
an ordinary four-example lesson. `workspace/semantic_probe.py` tests the
actual schedule, declarations, all cyclic starts, source hash, canonical
oracle agreement, exact-profile support, unique-input counts, and rival
refutation over 100 lessons per difficulty band.

## Deliberate domain limits

This generator supports target widths `3..8`, matching the canonical evidence
rather than claiming that a `2x2` maximum belongs to the reviewed training
domain. It teaches separated named competitors plus one-row zero noise; it does
not claim exhaustive coverage of arbitrary overlapping zero rectangles. Inputs
use at most three colors even though the rule itself is palette-invariant.

Imported baseline version: `2.0.0`. Reviewed version: `3.0.0`.
Approval remains a catalog/intake decision derived from current code and
retained evidence.
