# e1ec4585ab53

Fixed 6×6 grid with: (a) ROW 0 cells (0, 3) and (0, 5) hold COLUMN command codes (1..8); (b) COLUMN 0 cells (3, 0) and (5, 0) hold ROW command codes (1..8); (c) rows 3-5 × cols 3-5 hold a 3×3 SOURCE MOTIF with 3-6 cells in a single non-zero color. Rule (2×2 TRANSFORM MOSAIC): build a 2×2 grid of 3×3 mosaics. For each output position (r, c) in the 2×2: APPLY col_cmd[c] to the source, then row_cmd[r]. PACK the four 3×3 panels with 1-cell gaps. Output dims: 7×7 (2×3 + gap). Codes: 1=identity, 2=rotate CW, 3=rotate 180°, 4=transpose, 5=flip-LR, 6=flip-UD, 7=transpose (canonical duplicate), 8=anti-transpose. Net: row × col cmd grid yields a 2×2 transform mosaic of the 3×3 source.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
