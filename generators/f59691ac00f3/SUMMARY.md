# f59691ac00f3

Color-7 background grid. Row 0 contains a lawful 2/5 seed pattern and all lower rows start as 7. For each row r>0 and column c, read the two diagonal parents lp=(r-1,c-1) and rp=(r-1,c+1), using 7 outside the grid. If either parent is 7, keep 7. If lp==rp, write the opposite 2/5 color; otherwise write rp. Generated lessons always contain at least one active parent pair, so the output is never identical to the input.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
