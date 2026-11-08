# 33c7592c5cf0

0-bg grid (h, w ∈ 12-22, by difficulty) with: (a) ONE LR-SYMMETRIC MULTICOLOR BLOCK at the TOP (sr=1) — sh × sw (sh ∈ 3-5, sw ∈ 3-7, forced odd for exact symmetry), built via _make_sym_block: each row's cells set so row[c] == row[sw-1-c]; painted in colors drawn from a 4-color palette per PALETTE_KIND ∈ {warm, cool, broad, primary}; (b) N_ASYM ∈ 1-3 ASYMMETRIC DISTRACTOR BLOCKS placed BELOW the symmetric block (rows ≥ sr+sh+1) — each 2-3 × 2-4, with corners forced different so LR-symmetry is broken. All blocks placed with 1-cell halo padding via _can_place. Rule (EXTRACT EVERY 8-CONNECTED MULTICOLOR OBJECT; SORT BY (MIN_ROW, MIN_COL) ROW-MAJOR; OUTPUT THE FIRST LR-SYMMETRIC ONE — ITS BBOX CROP IN ITS ORIGINAL COLORS): EXTRACT every non-bg 8-conn object. SORT by (min_r, min_c). For EACH in order: CHECK if its normalized bbox-mask is LR-symmetric (row[c] == row[w-1-c]). SELECT the FIRST symmetric one. CROP to its bbox. OUTPUT the multicolor crop. Net: topmost-leftmost LR-symmetric object extracted; asymmetric distractors discarded.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
