# 81fdfd815936

0-bg grid (h ∈ 8-10, w ∈ 11-13) with: (a) ONE LR-SYMMETRIC BLOB at FIXED upper-left position (1, 1) — drawn as PLUS_5 shape (5-cell plus / +) in COLOR 4 (yellow); (b) ONE ASYMMETRIC DISTRACTOR at FIXED position (4, 7) — 4-cell L/Z shape [(0, 0), (0, 1), (1, 1), (2, 1)] in COLOR 5 (gray). Generation is deterministic for these positions × dims. Rule (AMONG ALL NON-BG OBJECTS, SORT BY (R1, C1) — TOP-MOST-THEN-LEFT-MOST. SELECT THE FIRST ONE WHOSE BBOX-MASK IS LR-SYMMETRIC (LEFT/RIGHT MIRROR EQUAL). OUTPUT THE BBOX CROP OF THAT SHAPE): EXTRACT all non-bg COMPONENTS. SORT by (top_row, left_col) ASCENDING. For EACH component in order: COMPUTE its bbox mask. CHECK if mask[r][c] == mask[r][bw-1-c] for all (r, c). SELECT the FIRST one with LR-symmetric bbox-mask. CROP that component to its bbox. OUTPUT the crop (in its original color). Net: LR-symmetric blob (the PLUS) is extracted; asymmetric distractor is discarded. Flagged hardcoded+intrinsic-low (uniq_in=9, uniq_out=1): fixed shape & color × few grid sizes → single canonical PLUS_5 crop output.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
