# 9971f3a5882c — sparse lattice boundary stretch

A color-3 rectangular lattice is represented by complete horizontal and vertical lines inside one bounding box. Exterior color-6 markers select sides to move: the nearest marker on each occupied side lies one cell beyond that side's new boundary. The source boundary line moves to the new coordinate, internal complete rows and columns stay fixed, and markers remain color 6.

Kind: `per_puzzle`. Reviewed version: `2.0.0`. Rule hash: `f753f2c684d9`.

## Observable controls

- `canvas_profile`: `c8x17`, `c11x15`, `c15x15`, `c16x17`, `broad18x19`
- `lattice_profile`: `frame3x3`, `cols3x5`, `rows4x3`, `lattice4x6`
- `marker_profile`: ten exact side/count profiles, including top markers and two markers on one side

All 200 exact control combinations are legal and recoverable from the returned input. Difficulty changes placement/expansion complexity but does not silently override an explicit profile.

## Teaching contract

The eight canonical pairs admit two simple rivals:

1. `ignore_top_markers` because no canonical input has a marker above the lattice.
2. `farthest_same_side_marker` because no canonical side has more than one marker.

The twelve-slot schedule alternates joint witnesses with ordinary examples. Every cyclic four-example window has two joint witnesses, so holding out any one example as the query leaves three demonstrations that refute both rivals. See `workspace/lesson_probe.py`.

Approval and training admission remain catalog decisions; this review does not change them.
