# b7ff231aab1a

Count the contiguous horizontal maroon (9) marker cells to obtain rank K. Find the three blue (1) 4-connected components, whose areas are strictly distinct; sort them by `(area, bbox top-left)`, select rank K (one-indexed), crop its bounding box, upscale 2×, and recolor every nonzero cell cyan (8).

Generated inputs use canonical colors and dimensions, random connected polyominoes, ten exact size profiles, and both complete derangements of area rank versus reading order. Thus the canonical-compatible reading-order rule is false on every generated sample.

Kind: `per_puzzle`. Reviewed version: `2.0.0`. Canonical rule hash: `5c4099040cb4`.
Approval remains derived by the catalog from current code and retained evidence.
