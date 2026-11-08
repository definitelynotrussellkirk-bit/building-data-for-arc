# 4e04b5fcae45

0-bg grid (h~10-16, w~12-18) with: (a) 1-3 HORIZONTALLY-SYMMETRIC COMPONENTS — each shape drawn from a small bank _SYM_H of LR-symmetric motifs (plus, square, horizontal-3 bar — shapes that satisfy shape ≡ flip_lr(shape)); (b) 2 ASYMMETRIC COMPONENTS — each shape drawn from _ASYM bank (L-triomino, Z-tetromino, T-shape — no LR symmetry). Each component is painted in a DISTINCT non-0 color drawn from {2, 3, 4, 6} (shuffled). Components are placed at non-touching positions with 1-cell padding (_free check). Rule (RECOLOR ONLY HORIZONTALLY-SYMMETRIC COMPONENTS TO COLOR 8): for EACH 4-CONNECTED non-bg COMPONENT in the input: CHECK whether the component's local shape (in its bbox) is HORIZONTALLY MIRROR-SYMMETRIC (flipping its cells left-right produces the same shape). If YES: RECOLOR every cell of that component to COLOR 8. If NO: LEAVE the component unchanged (keeps its original color). Bg-0 cells stay 0. Net: horizontally-symmetric shapes are unified under color 8 (cyan); asymmetric shapes retain their original colors as distractors.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
