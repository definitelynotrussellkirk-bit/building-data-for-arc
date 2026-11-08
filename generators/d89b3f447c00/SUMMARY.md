# d89b3f447c00

0-bg grid (h×w, ~7-15 by ~8-16) with 1-4 SAME-COLOR THREE-CORNER RECTANGLE CLUES. Each clue: same color appears at exactly 3 of 4 corners of some axis-aligned rectangle (the 4th corner is 0). Different rectangle clues use distinct colors. Clues are placed with ≥1-cell buffer (no 8-conn touch). Rule: for each color, examine all distinct (row, col) pairs from the color's cells. For every rectangle determined by 2 distinct rows and 2 distinct columns, if EXACTLY 3 of the 4 corners are this color and 1 is 0, paint the missing corner with that color. Each clue gets its 4th corner.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
