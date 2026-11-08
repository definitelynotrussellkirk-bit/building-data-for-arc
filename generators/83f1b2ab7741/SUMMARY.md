# 83f1b2ab7741

0-bg grid (h~10-13, w~12-16) containing: (a) EXACTLY ONE PAIR of COLOR-6 (magenta) MOTIFS where the second is a HORIZONTAL MIRROR of the first (asymmetric base shape such that mirror differs from original); (b) 0-2 additional COLOR-6 distractor motifs that are NEITHER the base nor its mirror (different normalized shape); (c) 1-3 distractor MOTIFS in OTHER non-{0, 6} colors (2-4 cells each) placed at scattered positions. All motifs are non-touching (1-cell padding). Rule: among all color-6 components, find the UNIQUE PAIR (A, B) where normalize(B) = h_mirror(normalize(A)). RECOLOR both A and B to COLOR 2 (red). ERASE everything else (set all other cells, including other color-6 distractors and other-colored motifs, to 0). Net: only the unique horizontally-mirrored magenta pair survives, repainted red.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
