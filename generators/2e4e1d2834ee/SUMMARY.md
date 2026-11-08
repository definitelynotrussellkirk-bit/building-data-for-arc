# 2e4e1d2834ee

h × (3*w+2) grid (0-bg, h=5..6, w=5..6) with THREE same-size w-column panels separated by full-height color-9 (maroon) divider columns. Each panel contains a different count of occupied cells (e.g., 3, 5, 8) in DIFFERENT colors (one color per panel, all distinct from 0 and 9). One panel is the STRICT WINNER (most cells). Rule: split panels at color-9 cols. Count occupied (non-zero) cells per panel. Pick the panel with the most cells. Recolor all its cells to 8 (cyan). Output: just that panel (cropped, w columns wide, h rows tall) with original positions kept and color 8 in non-zero slots.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
