# 5a09c683cd25

0-bg grid (size varies). Cell (0,0) holds a COLOR KEY. The grid contains ONE LR-SYMMETRIC target blob (a random connected LR-symmetric polyomino, 3-14 cells, its own color) and 1-3 LR-ASYMMETRIC distractor blobs (each a random asymmetric polyomino in a distinct color). All blobs are placed non-touching (8-connectivity gap) so they are separate components, and none sits at (0,0). Rule (SELECT LR-SYMMETRIC BLOB, CROP + RECOLOR TO KEY): read the key color at (0,0); zero it; among all objects keep those whose cropped binary mask equals its flip-lr; take the smallest; crop to bbox; recolor every cell to the KEY color. Output = the symmetric blob's shape painted in the key color. Distractors (asymmetric) are never candidates, so the symmetric target is always the one selected.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
