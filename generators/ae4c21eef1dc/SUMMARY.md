# ae4c21eef1dc

0-bg grid (h~9-11, w~11-13) with 3-4 scattered SMALL MOTIFS in distinct non-bg colors. Canonical rule layout (NOT yet matched by this generator): the grid is split HORIZONTALLY by FULL-HEIGHT color-5 (gray) DIVIDER COLUMNS into THREE 5×5 panels (left, middle, right). Left and middle carry colored cells; right is empty in input. Rule: for each cell (r, c) ∈ (5 × 5), compute the right panel as: if BOTH left[r][c] and middle[r][c] are non-zero, output 8 (collision marker); if only ONE is non-zero, output that color; else output 0. Re-join the three panels with color-5 separators. Net: a 3-panel layout where the right panel is the COLORED OR-OVERLAY of left and middle, with cyan marking conflicts.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
