# fcabbbbdfc11

0-bg grid (h 5..14, w 12..22): row 0 is a legend listing 2..5 distinct non-zero colors by default (1..5 including the one_color edge) at scattered columns (left-to-right = pack order, always different from the below reading order when >=2 colors); row 1 is empty; rows 2..h-1 hold one 4-connected polyomino piece (1..5 cells canonical, up to 6 on generalized draws; bbox <= 3x3) per legend color, plus optional duplicate-color pieces (rule selects the LAST per color) and non-legend distractor pieces (rule ignores them). Output: the last piece per legend color cropped to its bbox and packed horizontally in legend order with 1-column zero gaps.

Kind: `per_puzzle`. Imported version: `3.4.0`.
Approval is derived by the catalog from current code and retained evidence.
