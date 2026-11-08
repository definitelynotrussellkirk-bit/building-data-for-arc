# Parametric prototype: e06cc4c752b2

- `finish=canonical` returns the exact selected singleton-to-horizontal-bar program.
- `finish=fill_largest_bbox` runs that expansion as stage A, then fills the bounding box of the largest expanded same-color component with color 9.
- The input grammar builds a same-color diagonal staircase of singleton markers. The markers are cardinally isolated before stage A; their horizontal bars become one connected component only after expansion. Smaller expanded chains and singleton distractors make largest-component selection necessary.
- Inputs are matched across settings and count-independent. Qualification uses two demonstrations and four queries; the fourth query is 30×30.
