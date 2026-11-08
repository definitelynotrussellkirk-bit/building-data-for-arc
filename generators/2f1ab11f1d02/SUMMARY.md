# 2f1ab11f1d02

0-bg grid (h ∈ 7-9, w ∈ 9-11) with: (a) ONE CMD CELL at FIXED position (0, 0) — value ∈ {1..7} selecting a TRANSFORM (1=identity, 2=cw90, 3=180, 4=ccw90, 5=flip-LR, 6=flip-UD, 7=transpose); (b) ONE SMALL MULTICOLOR BLOB in the LOWER-RIGHT QUADRANT — sub_h × sub_w (sub_h, sub_w ∈ 2-3 with sub_h ≠ sub_w to make transforms visible) at random position (r0 ∈ h//2..h-sub_h-1, c0 ∈ w//2..w-sub_w-1), with each cell painted (with 70% prob) in one of 2 distinct palette colors drawn from {2..9}\{cmd}. Rule (READ THE CMD AT (0, 0), CLEAR (0, 0) TO 0, CROP THE BODY TO NON-BG CONTENT, APPLY TRANSFORM BY CODE — 1=IDENTITY, 2=CW, 3=180, 4=CCW, 5=FLIP-LR, 6=FLIP-UD, ELSE=TRANSPOSE — OUTPUT THE TRANSFORMED CROP): READ cmd from (0, 0). SET (0, 0) = 0. CROP the remaining grid to the bbox of non-bg cells. APPLY the cmd's TRANSFORM. OUTPUT the transformed crop. Net: corner cmd selects 1 of 7 dihedral operations on the cropped multicolor blob.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
