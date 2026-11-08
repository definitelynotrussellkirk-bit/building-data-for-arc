# 0d877a4c52fd

A 6–12 by 6–12 zero-background grid contains exactly two or three distinct foreground colors. Each color appears at exactly three corners of one axis-aligned rectangle; the implied fourth corner is blank, and implied corner sets are disjoint. The rule paints each missing corner with its rectangle's own color and leaves every other cell unchanged.

The default sampler deliberately keeps exact canonical support (9×9 with two or three colors) while also emitting adjacent-side, spaced-side, and mixed rectangles. Three demonstrations are used. Their deterministic schedule exposes every missing-corner orientation and refutes the canonical-fitting shortcut “complete only rectangles whose row and column spans are both at least two,” including under every held-out query rotation tested by the census.

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule pin: `bf8c9dd4f7fa`.
