# beb87e1c1b19

FIXED 3×11 grid with: (a) THREE 3×3 PANELS separated by FULL-HEIGHT COLOR-8 (cyan) DIVIDER COLUMNS at cols 3 and 7. Panels A (cols 0-2), B (cols 4-6), C (cols 8-10). PANEL A is a fixed L-shape (cells (0,0), (1,0), (1,1)) recolored in random non-{0, 8} A-COLOR. PANEL B is the same L-shape transformed by a chosen transform CODE (r1=rot90CW, r2=180, r3=CCW, fh=flip LR, fv=flip UD, tr=transpose, atr=anti-transpose) recolored in B-COLOR. PANEL C is a different fixed shape (cells (0,2), (1,1), (1,2)) recolored in C-COLOR. Rule (INFER TRANSFORM FROM A→B, APPLY TO C, UNION WITH ORIGINAL C): compare the support (cell positions) of PANEL A and PANEL B — infer which dihedral transform T maps A's support to B's. APPLY T to PANEL C's support. OVERLAY the transformed C cells (painted in C's color) onto the original C panel — nonzero transformed cells overwrite bg in C. Net: C panel gets enriched with T-transformed copies of itself. Flag: INTRINSIC-LOW DIVERSITY — fixed shapes × 7 transforms × small color set → ~19 distinct outputs.

Kind: `per_puzzle`. Imported version: `2.3.0`.
Approval is derived by the catalog from current code and retained evidence.
