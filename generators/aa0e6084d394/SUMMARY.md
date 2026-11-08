# aa0e6084d394

0-bg grid (h~7-14, w~8-16) with 1-3 ISOLATED non-bg cells, each in a distinct color (no color-2 in input). Cells are placed at distinct rows AND distinct columns. Rule: for each non-bg cell at (r, c) with color v, PAINT a full CROSS — every cell in row r and every cell in column c — with color v. Where TWO CROSSES OVERLAP (a cell sits on row(a) ∩ col(b) or row(b) ∩ col(a) for two different seeds), PAINT that intersection cell with color 2 (red) — the conflict marker — OVERRIDING the per-seed color. The original seed cells stay their own color. Net: input has isolated colored dots; output has full cross shapes per dot with red marking where two crosses cross-intersect.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
