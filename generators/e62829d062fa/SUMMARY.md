# e62829d062fa

0-bg grid (h~8-10, w~9-11) with: (a) TRANSFORM CODE at (0, 0) in COLOR ∈ {1, 2, 3, 4, 5} encoding rotation/flip (1=IDENTITY, 2=ROT CW, 3=ROT 180, 4=ROT CCW, 5=FLIP LR or similar); (b) TARGET COLOR at (0, w-1) in some non-{0, code, body_color} color (the destination color for the transformed body); (c) BODY SHAPE — one ASYMMETRIC SHAPE from a small bank (L-tetromino, T-tetromino, S-tetromino) in a DISTINCT non-{0, code, target} color at random interior position. Rule (CROP THE BODY SHAPE, TRANSFORM PER CODE, RECOLOR TO TARGET COLOR): READ the CODE from (0, 0) and TARGET COLOR from (0, w-1). CROP the body shape to its BBOX. APPLY the transform encoded by CODE. RECOLOR all non-bg cells in the transformed crop to TARGET COLOR. OUTPUT is the transformed + recolored body. Code, target, and original body are discarded. Net: the body is rotated/flipped per code and painted in the target color.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
