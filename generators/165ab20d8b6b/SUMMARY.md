# 165ab20d8b6b

A zero-background grid contains 1–4 isolated, distinctly colored, interior 4-connected blobs. For each blob, erase its original cells and paint every zero cell immediately adjacent in the four cardinal directions with that blob’s color. Generated blobs have disjoint shells, so each output cell has one owner.

Version `3.0.0` supports exact, observable controls for grid height (8–14), grid width (9–16), blob count (1–4), and scene profile (`canonical`, `broad`, `hole_witness`). The default lesson schedule includes enclosed-hole ring witnesses that distinguish the intended local rule from the canonical shortcut that paints only exterior-connected background cells.

The selected canonical Racket rule remains label authority and is pinned by `RULE_HASH = "63879e6d755e"`.
