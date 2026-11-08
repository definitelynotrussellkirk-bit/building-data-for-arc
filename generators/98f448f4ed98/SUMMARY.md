# 98f448f4ed98

0-bg grid (h~9-11, w~13-15) with: (a) ROW 0 holds k COLOR-2 (red) CELLS (k=4-5) at random distinct columns; (b) TWO HOLLOW COLOR-4 (yellow) RECT-OUTLINE FRAMES — FRAME A at (1..5, 1..k) with WIDTH = k (matches); FRAME B at (2..6, w-other_k-1..w-2) with WIDTH = k+1 or k-1 (mismatches). Rule (FILL 4-FRAME INTERIOR WITH 8 IF FRAME WIDTH EQUALS k): COUNT k = number of COLOR-2 cells in row 0. For EACH COLOR-4 FRAME: if frame WIDTH equals k, FILL its INTERIOR cells with COLOR-8 (cyan). Non-matching frames stay empty. Frame outlines stay 4. Net: only the frame whose width matches the red count fills with cyan.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
