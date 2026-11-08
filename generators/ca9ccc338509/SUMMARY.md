# ca9ccc338509

Input is (N+1) × (M+1). Row 0 cols 1..M hold M col-key colors; col 0 rows 1..N hold N row-key colors. (0,0) is 0. Rule emits a 2N × 2M grid: at output (r, c), use row-key[r//2] if (r+c) is even, else col-key[c//2]. The output is a 2-cell-thick checkerboard mixing the row and col keys.

Kind: `per_puzzle`. Imported version: `1.2.2`.
Approval is derived by the catalog from current code and retained evidence.
