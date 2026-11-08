# 48e1e7f40749

Fixed 10×11 grid with: (a) ROW 0 cols 0-2 hold 3 DISTINCT PALETTE COLORS (rest 0); (b) ROWS 1-2 cols 0-1 hold 4 SELECTOR cells (values 1..3 referencing bank keys); (c) ROWS 3-4 cols 0-1 hold 4 TRANSFORM COMMAND codes (0..5); (d) ROW 6 cols 0, 4, 8 hold 3 BANK KEYS (values 1, 2, 3); (e) ROWS 7-9 cols kcol..kcol+2 hold three 3×3 TEMPLATES anchored at each bank key column with ~50% sparsity. Rest is 0. Rule (PALETTE-LIFT MATRIX WITH TRANSFORMS): for EACH of 4 SELECTOR positions, look up the bank template by the selector's key, APPLY the transform indexed by the matching command, RECOLOR using the row-0 palette, and assemble all four results into a 6×6 2×2 MOSAIC. Output: 6×6 mosaic of 4 transformed 3×3 palette-lifted templates. Net: matrix-of-templates addressed by selector × command → 2×2 mosaic with palette-colored cells.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
