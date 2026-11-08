# Generator 297c05190f7c

On a 0-background grid, each nonzero same-color **4-connected component** is a
separate object. The output fills that component's tight bounding box with its
color. Components are never merged merely because they share a color or touch
diagonally.

Kind: `per_puzzle`. Selected version: `2.3.0`. The Racket authority, canonical
rows, public axes, period-three profile schedule, and
`RULE_HASH = 3cad5a2fcf1f` are unchanged.

## Teaching distribution

The three scheduled profiles now cover both the public scale and the strongest
canonical-fitting shortcuts found in three adversarial passes:

- `canonical_pair`: two different-colored irregular objects. Alternating
  appearances use either a sparse 6x8/8x6 L (13 cells, fill gain 35, deep
  missing cells) or a canonical-scale 3x5/5x3 L (7 cells). The small branch
  keeps public component sizes reachable while still refuting one-step-fill,
  minimum-density, gain, aspect, and extent filters.
- `component_split`: a canonical-query-style diagonal same-color split plus a
  2x8/8x2 irregular object. This distinguishes 4- from 8-connectivity,
  per-component from per-color processing, and elongated from near-square
  filters.
- `expanded`: four components. A dense 23-cell holed 5x5 object crosses
  thickness, cycle, hole, density, and size boundaries. A nearby unequal
  same-color irregular component defeats conditional “largest per color”
  grouping while two other components preserve all-object and non-corner
  evidence.

The generator contains executable rivals for identity, per-color merging,
8-connectivity, largest-only, location/extent restrictions, five topology and
density filters, and eight round-three geometry/grouping filters. Semantic
witnesses and lesson checks compare every named distinction against the exact
per-component bounding-box output.

## Review tools

`workspace/distribution_probe.py` retains the original spatial/extent audit.
`workspace/shortcut_miner.py` independently reconstructs components, intended
outputs, and 18 declared rivals without calling the selected generator's
private analyzer, mirror, witnesses, or rival functions. Reports include source
hashes, denominators, unique-input counts, property support, disagreement
counts, and first exact counterexamples.

Exact 2.0.0, 2.1.0, and 2.2.0 generator sources are retained for reproducible
before/after replay. The round-three review also used an external 127-candidate
search spanning fill depth, gain, density, scale, aspect ratio, and same-color
selection conditionals; it is packaged as review evidence rather than selected
runtime code.
