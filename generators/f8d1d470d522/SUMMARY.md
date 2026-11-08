# f8d1d470d522

Construct a branching color-8 route network between two color-9 markers. Color-7 obstacles disable cardinally adjacent 8 cells and thereby alter the route. Select a legal route by shortest length first and fewest turns second, then paint that unique route color 9 while leaving unused branches unchanged.

Default five-demo curricula cycle through two generated semantic anchors, two exact canonical-profile draws, and one general draw. The anchors explicitly distinguish obstacle-aware routing, the fewest-turn tie-break, and the canonical-fitting `bottommost_shortest` shortcut under every supported query rotation.

An isolated prototype under `workspace/parametric/` varies `turn_preference` between canonical `fewest` and proposed `most`; it does not change selected production execution.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
