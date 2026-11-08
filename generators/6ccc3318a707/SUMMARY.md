# 6ccc3318a707

Reflect the entire square grid across the anti-diagonal. Every cell at `(r,c)` moves to `(n-1-c,n-1-r)`; anti-diagonal cells are fixed. Ordinary draws are 6×6, 7×7, or 8×8 with exactly four foreground colors and deliberately include fixed points, singleton mirror orbits, differently colored occupied mirror pairs, and repeated colors. Those cases distinguish the selected move rule from copy/overlay, collision-skipping, unique-color-only, and main-diagonal shortcuts.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `ea62a41435bf`.
