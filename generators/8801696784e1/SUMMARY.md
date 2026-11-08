# 8801696784e1

0-bg grid (h~9-11, w~11-13) with: (a) TRANSFORM CODE at (h-1, w-1) in value {1, 2, 3} (encodes rotation 0°/90°/180° or similar); (b) ONE LR+UD-SYMMETRIC SHAPE drawn from 3 hardcoded SYMMETRIC TEMPLATES (3×3 frame, +cross, X-pattern) in a random color from {2, 4, 5, 6, 7, 8, 9}; (c) ONE ASYMMETRIC SHAPE drawn from 3 hardcoded ASYM TEMPLATES (L-shape, corner-tromino, J-shape) in a distinct random color. Shapes placed non-overlapping with 1-cell padding. Output uniq_out=17 (intrinsic — 3 symmetric templates × 3 codes × upscale normalizes). Rule (PICK SYMMETRIC SHAPE, TRANSFORM BY CODE, UPSCALE 2x): identify the CODE at (h-1, w-1). AMONG components whose CROP is BOTH LR- AND UD-SYMMETRIC, PICK the LARGEST. APPLY the CODE's TRANSFORM (rotation/flip) to that crop. UPSCALE 2× (double dims). EMIT the result as output. Net: largest LR+UD-sym shape, transformed and 2× upscaled.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
