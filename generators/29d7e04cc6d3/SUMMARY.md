# 29d7e04cc6d3

0-bg grid (h~7-10, w~7-11) with EXACTLY TWO separated connected motifs in distinct nonzero colors. Each motif has a small 2-3 by 2-3 bbox and 3 cells. Rule (TWO-MOTIF OVERLAY): detect the two connected objects, crop each to its bbox, align both crops at the top-left of a fresh canvas whose height/width are the max crop dimensions, copy object colors into non-overlap cells, and paint overlap cells color 8. Net: two scattered motifs become one aligned overlay mask. Normal generation never emits a third motif because the canonical rule consumes only the first two objects.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
