# 174d775fd42f

Fixed 7×7 0-bg grid with: (a) TWO FULL HORIZONTAL DIVIDER ROWS at rows 2 and 5, each painted entirely in a SINGLE non-zero hline_color; (b) TWO VERTICAL DIVIDER COLUMNS at cols 2 and 5, each containing the same COLOR (v1 for col 2, v2 for col 5) at ALL non-divider rows (rows 0, 1, 3, 4, 6). hline_color, v1, and v2 are 3 distinct non-zero colors. Other cells are 0. Rule: DETECT the FULL NONZERO horizontal DIVIDER ROWS and the CONSTANT vertical DIVIDER COLUMNS. COMPRESS the 7×7 grid into a REPRESENTATIVE smaller grid: keep only ONE REPRESENTATIVE ROW per group between horizontal dividers, and ONE REPRESENTATIVE COL per group between vertical dividers. The dividers themselves are stripped; output is the intersection-cells matrix. Net: input is a divider-decorated grid; output is its compressed form (group representatives only).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
