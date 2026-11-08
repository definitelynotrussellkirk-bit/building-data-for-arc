# b4b628596579

Dense color grid (h~4-9, w~6-12) where each ROW is a CYCLIC SHIFT of one base color sequence: row 0 = the base sequence (a length-w row drawn from a rich 4-9 color non-0 palette by default), and every other row is an independent non-zero cyclic shift of the base (so it differs from row 0). Rule: replace every row with row 0 (broadcast the top row to all rows). The output is therefore w-wide and entirely row-0's pattern repeated; its diversity comes from the base sequence in row 0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
