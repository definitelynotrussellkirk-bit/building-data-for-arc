# 371eb0221101

A 7..14 × 7..14 zero-background grid contains 2..4 isolated monochrome
L-triominoes.  Each object is exactly three corners of a tight 2×2 box and has
a one-cell moat from every other object.  Inputs use 1..2 nonzero colors.

The rule rotates **every** L-triomino 90° clockwise in place inside its own
2×2 bounding box, preserving color.  The repaired sampler exposes exact
controls for height, width, object count, and distinct-color count, retains
canonical profile support, and deliberately emits non-6 objects to distinguish
the intended rule from the canonical-fitting “rotate color 6 only” shortcut.

Kind: `per_puzzle`. Selected generator version: `3.0.0`. Canonical Racket
authority is unchanged and pinned by `RULE_HASH = "27c74d38508a"`.
