# 1c2f874f3e82 — anchor-relative transform stamps

A connected asymmetric color-2 source is encoded as signed offsets from one
color-1 anchor. Each color-3 marker stamps those offsets unchanged, color 4 stamps
a clockwise quarter-turn, and color 5 stamps a vertical mirror; output cells are
color 8.

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash:
`bb27569b9c6f`.

Exact controls vary grid height 10–14, grid width 16–20, source size 3–7, and
marker count 3–5. A seven-slot four-demonstration curriculum guarantees examples
that refute fixed-four/cap-five source truncation and first-marker-only shortcuts.
All generated stamps are complete, in bounds, pairwise disjoint, and disjoint from
input symbols.
