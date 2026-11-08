# 75381adf158d

Version `3.0.0` constructively generates zero-background grids containing
separated colored rectangular frames.  Closed frames enclose zero-regions;
open frames omit one outward side and remain connected to the exterior.  The
canonical rule fills every border-inaccessible zero cell with cyan (`8`) while
leaving frame cells and border-connected zero-regions unchanged.

The generator exposes only three exact controls: `grid_h` in 10–30, `grid_w`
in 12–30, and `scene_profile` in `mixed`, `largest_counterexample`, or
`many_holes`.  Unknown or incompatible overrides fail loudly.  A Python
flood-fill mirror, structural analysis, override observer, and strict
self-check cover the production contract.  Ordinary draws span 10×12 through
30×30 and always include both an enclosed region and an exterior-connected
zero-region.

The native parametric family preserves the selected canonical Racket program
byte-for-byte and adds `largest_escape`: after canonical filling, the unique
largest newly created cyan component is selected and connected from its center
to the nearest grid border by a straight cyan route.  A protected
smallest-component counterfactual establishes the intermediate dependency.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
