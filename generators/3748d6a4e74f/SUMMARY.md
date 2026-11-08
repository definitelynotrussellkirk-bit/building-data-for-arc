# 3748d6a4e74f

0-bg grid (h ∈ 8-10, w ∈ 8-10) with: (a) ONE CMD CELL at FIXED position (0, 0) — value ∈ {1, 2, 3, 4} selecting a rotation (per demos: 1=cw90, 2=180, 3=ccw90, 4=identity); (b) ONE SINGLE NON-RECTANGULAR BLOB in a non-cmd color drawn via draw_color: a SIZE ∈ 4-7 cell irregular blob built by grow_blob random walk, placed so NONE of its cells lie in the 2×2 corner around (0, 0) (so cmd stays isolated). Rule (READ THE CMD, CROP THE BLOB TO ITS BBOX, ROTATE BY THE CMD VALUE): READ cmd from (0, 0) → select rotation. FIND the single non-bg blob (excluding the cmd cell). CROP the blob to its bounding box (a small h_bb × w_bb grid with the blob's color where cells are present, 0 elsewhere). ROTATE the cropped grid by cmd (cw90 / 180 / ccw90 / identity). OUTPUT the rotated crop. Net: a single colored shape is extracted and rotated by the corner code, yielding a small output grid.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
