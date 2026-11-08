# 9fbd0923e6ae

A zero-background grid contains a nonzero, non-gray target-color selector at `(0, 0)`, exactly one complete gray (`5`) guide row or column, 2–7 additional target-color cells, 2–6 distractor cells in one or two other colors, and 0–3 isolated gray noise cells. The guide may be at the one-third, middle, or two-thirds position; target cells may be on the selector side, the opposite side, or both sides.

Rule: preserve the input and reflect every target-color cell **except** the selector across the complete gray guide. Paint the reflected coordinate when it is in bounds; ignore out-of-bounds mirrors. The operation is bidirectional, so target cells on either side can paint the other side. A lawful scheduled profile has only clipped mirrors and therefore an identity output.

The deterministic six-profile curriculum covers vertical and horizontal guides, canonical dimensions and 4/5-color palettes, off-center guides, both source sides, identity/clipping, isolated gray noise, and cyclic-query-safe counterexamples to the canonical-compatible “selector-side-only” rival.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical rule hash: `63d7f8006f35`.
