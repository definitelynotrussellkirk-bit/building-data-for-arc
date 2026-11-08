# 35c7e1c0d116

0-bg grid (h~4-5, w derived) with N=3-4 same-height PANELS each of width 4, separated by FULL COLOR-9 (maroon) DIVIDER COLUMNS of width 1. Each panel holds a CONNECTED MOTIF of 2-4 cells in some non-{0, 9} color (distinct per panel). Output uniq_out=16 (intrinsic — N×N binary match matrices normalize). Rule (BUILD DIHEDRAL-MATCH MATRIX): identify the N PANELS separated by 9-dividers. EMIT an N×N OUTPUT GRID where out[r][c] = 8 if PANEL-r's NORMALIZED MOTIF CELLS match ANY DIHEDRAL VARIANT (8 transforms — 4 rotations × 2 flips) of PANEL-c's MOTIF CELLS. Else 0. Net: pairwise shape-equivalence matrix across panels modulo D4.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
