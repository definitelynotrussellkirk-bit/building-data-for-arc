# Current notes: a286d31d63fb

## Accepted rule and source identity

The canonical Racket authority is unchanged. Its rule hash is `bc2002d0a0d4`
(full recorded canonical hash `bc2002d0a0d4dd9628242b448e63f2a988832268d371b2f1b03c7540d031e7ac`).
For each monochromatic 4-connected nonzero component, count occupied cells in
each occupied row; recolor the component to 8 exactly when those counts are all
equal. Generator version `3.0.0` pins that authority. Final generator SHA-256:
`4226cd30d3bcb427a8b39aa49b368cc6c6deffc3cc5ce4737ea28128b9ec82a2`.

## Repair decisions

The prior source advertised controls it did not consistently implement, accepted
unknown/ill-typed values, used a degenerate all-flat path that violated its own
validator, and taught only solid rectangular positive examples. The replacement
keeps only five public controls with exact behavior in every difficulty band:

- `height`: integer 8..16
- `width`: integer 11..18
- `flat_component_count`: integer 1..3
- `nonflat_component_count`: integer 1..2
- `palette_kind`: `default|warm|cool|varied`

Unknown axes and the retired `texture`, `palette_size`, `n_distinct_colors`,
`position_bias`, and `density` controls are rejected. Seeds/sample indices and
numeric overrides require actual integers rather than accepting booleans,
strings, or floats. `observe_overrides` recovers both exact component-count axes
from returned grids.

Placement is now a constructive two-lane packer rather than a capped retry loop.
It supports the complete declared domain, including an 8x11 canvas with five
components. Distinct source colors prevent accidental same-color component
merges. Defaults retain canonical 9x15 and 10x16 scales and the canonical-like
2-flat/1-nonflat profile in every band.

Every generated lesson contains at least one connected nonrectangular component
with a constant row profile. `rectangle_only` is declared in
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; the
`nonrectangular_flat_profile` witness explicitly claims and verifies that rival
through `WITNESS_RIVALS`. The retained fixture
`counterexamples/rectangle_only.json` is the compact concrete separator.

`self_check` now fails closed on malformed/ragged/non-integer/out-of-range grids,
reserved input color 8, repeated disconnected uses of a source color, and scenes
missing either semantic class. It intentionally accepts the canonical examples,
which need not contain the newer curriculum witness.

## Verification on the final source

- Portable staged tests: 59 passed.
- `lint`, strict `defect_lint`, `selfcheck`, and live `rule_smoke`: passed.
- Override contract: 25,200/25,200 draws accepted with zero findings.
- Semantic gate: 600 generated lessons; the declared nonrectangular witness and
  rectangle-only disagreement were verified throughout.
- Independent adversarial probe: 768 boundary draws across all bands, both
  numeric endpoints, count endpoints, all palettes, and three seeds; zero
  findings and 188 distinct inputs.
- Canonical Racket parity: minimum-canvas/max-count, maximum-canvas/max-count,
  canonical-scale, and retained-witness inputs all matched the independent
  row-profile oracle and disagreed with the rectangle-only rival.

Evidence is retained under `WORK/checks/a286d31d63fb-*`; the reusable bounded
probe is `workspace/adversarial_probe.py`.

## Limits and next action

The sampler deliberately uses a finite, compact shape bank with reflections; it
is not a claim that all lawful polyominoes or all possible rival hypotheses are
covered. The three canonical pairs themselves remain answer-equivalent under the
rectangle-only shortcut, so generated counterexamples carry that teaching load.
The declared rival set is targeted, not a universal lesson-identifiability proof.
Packaging this repair does not grant training admission or catalog approval.

Next action: ingest the delta and preserve the final-source receipts when
resolving the two old source-bound audits; no canonical Racket change is needed.
