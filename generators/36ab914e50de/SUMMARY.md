# 36ab914e50de

A 2x2 lattice of 3x3 tiles separated by color-9 dividers (7x7). Each tile carries EDGE-CENTER CONNECTOR colors on its inward-facing edges and a CENTER color; the solved lattice matches connectors across every internal seam (4 distinct connector colors, 4 distinct centers, all 8 colors random). The four tiles are then SCRAMBLED — permuted into the 4 slots and each randomly rotated. Rule: search permutations x rotations for the 2x2 arrangement whose touching edge-centers all match, and output that assembled lattice (lex-min valid orientation). The colors drive the OUTPUT and the scramble drives the INPUT, so both vary freely (was 4 fixed tiles with 6 hardcoded scrambles).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
