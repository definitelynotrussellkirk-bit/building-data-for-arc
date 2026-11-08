# db8923f18bcc

0-bg grid (h~6-8, w~6-8) with 2-4 ISOLATED L-TRIOMINOES — each is a 2×2 window with EXACTLY 3 of the 4 cells painted in ONE non-0 color from {1..9}; the FOURTH (missing) CORNER is 0. Which of the 4 corners is missing is random per triomino. Triominoes are placed at non-touching positions with 1-cell 8-conn padding (so each L-shape sits alone in its 2×2 window, no shared cells between any two). If random placement fails entirely, generator emits a single fallback L at (1,1)-(2,1). Rule (FILL MISSING CORNER OF EACH MONOCHROME L INTO A 2×2 SQUARE): For EACH 2×2 WINDOW where exactly 3 cells share ONE non-0 color C and the fourth cell is 0: RECOLOR the missing-corner 0 cell to C, completing the 2×2 monochrome square. Other cells (already filled with C, or outside any active 2×2 window) stay unchanged. Net: every L-triomino is closed into a solid 2×2 monochrome block of its own color.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
