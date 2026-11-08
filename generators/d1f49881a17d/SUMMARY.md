# d1f49881a17d

0-bg grid (h, w~10-13) with: (a) A SINGLETON MARKER — single cell at (1, w-2) (top-right interior) in a chosen shared color C from {2, 3, 4, 6, 7, 8, 9}; (b) A LARGER OBJECT of the SAME color C — a 4-5 cell shape drawn from a shape bank, placed near the bottom-left at anchor (h-5, 1); (c) A DISTRACTOR L-tromino of COLOR 5 at fixed top-left (rows 2-3, cols 2-3) in a different color. Rule (CROP LARGER OBJECT MATCHING THE MARKER COLOR, CENTER ON BLANK CANVAS OF ORIGINAL SIZE): find the SINGLETON MARKER (a single cell) — its color is C. Find the LARGER OBJECT (≥2 cells) sharing color C (4-connected component). EXTRACT its bbox crop, then PAINT it CENTERED on a fresh blank canvas of the ORIGINAL h × w dimensions (centered at ((h - bbox_h)//2, (w - bbox_w)//2)). Marker and distractor objects are discarded. Net: only the matching larger object survives, centered on a blank canvas.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
