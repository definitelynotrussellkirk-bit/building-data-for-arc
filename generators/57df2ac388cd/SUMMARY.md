# 57df2ac388cd

0-bg grid (size varies) with EXACTLY 2 isolated 4-connected MOTIFS in distinct non-{0,8} colors (3-6 cells each), placed apart by >=1 bg cell. The two motifs' NORMALIZED forms (cropped to top-left) share at least one cell. Rule: take the first 2 objects in scan order; normalize each to its bbox top-left; output a max(h_a,h_b) x max(w_a,w_b) grid where a cell in BOTH shapes -> 8 (cyan), only in A -> color A, only in B -> color B, else 0. Net: overlay the two motifs aligned at top-left, overlap shown cyan.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
