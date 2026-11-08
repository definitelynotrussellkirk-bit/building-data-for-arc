# 5779a70a36ff

0-bg grid (size varies) with EXACTLY 2 isolated 4-connected MOTIFS in distinct non-0 colors (3-6 cells each), placed apart by >=1 bg cell. The two motifs' NORMALIZED shapes are mutually non-subset. Rule: take the first 2 objects sorted by bbox (col, then row); A = leftmost/topmost. Normalize each; output a max(h_a,h_b) x max(w_a,w_b) grid with A's cells that are NOT in B painted in A's color, rest 0. Net: set-difference A-minus-B of the two aligned shapes, in A's color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
