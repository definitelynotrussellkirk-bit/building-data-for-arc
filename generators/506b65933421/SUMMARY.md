# 506b65933421

0-bg grid (h~5-7, w~9-11) with ONE COLOR appearing as EXACTLY 2 CELLS placed at DIAGONAL positions forming a NON-DEGENERATE BBOX (≥3 rows AND ≥3+ cols span). The two cells are at (r1, c1) and (r2, c2) with r2 ≥ r1 + 2 and c2 ≥ c1 + 3 (or other diagonal arrangement). Color chosen from {2..9}. Rule (FILL EACH 2-CELL COLOR'S BBOX RECTANGLE WITH THE COLOR ON A FRESH EMPTY GRID): For EACH COLOR appearing ≥2 times (here, exactly 2): compute its BBOX (min/max row and col). PAINT every cell within the bbox (inclusive) with that color in the output. Other cells stay 0. Net: the 2 cells get filled in to the solid rectangle they define.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
