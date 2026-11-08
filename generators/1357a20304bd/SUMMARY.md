# 1357a20304bd

Variable-size 0-bg grid with 1-4 foreground colors, each placed as 2-4 ISOLATED SEED POINTS at random distinct positions. Rule (CONNECT SAME-COLORED POINTS IN READING ORDER WITH HORIZONTAL-THEN-VERTICAL TRACES): For EACH COLOR with ≥2 SEED POINTS: sort points in READING ORDER (row-major). For consecutive pairs (p_i, p_{i+1}): draw a horizontal-then-vertical L-PATH from p_i to p_{i+1} — first move HORIZONTALLY from p_i's column to p_{i+1}'s column on p_i's row, then VERTICALLY from p_i's row to p_{i+1}'s row on p_{i+1}'s column. PAINT all path cells in that color. Net: same-color points chain together via row-major-ordered L-paths.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
