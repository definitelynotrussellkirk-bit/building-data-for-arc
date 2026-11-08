# 5a01897eb8be

A 13–24 by 17–24 grid uses its top-left value as background and contains 3–6 differently colored corner glyphs. For each color, the intended rule measures the glyph’s bounding-box maximum dimension and its longest monochrome corner arm. The maximum dimension assigns that color to the smallest available odd ring that fits (loose fits first, then exact fits largest-first); the arm length determines how much of each of the output ring’s four corners is colored.

The sampler covers center/no-center outputs, exact and loose allocation, arbitrary ARC backgrounds, partial/multi-corner glyphs, canonical size/palette anchors and broader dimensions. Placement is randomized so row-major first appearance does not reveal ring order, and partial arms refute a solid-border shortcut. Lessons use three demonstrations and one query with executable scan-order and solid-ring competitors.

Kind: `per_puzzle`. Current generator version: `3.0.0`. Pinned rule hash: `00935b1c1bf9`.
Approval is derived by the catalog from current code and retained evidence.
