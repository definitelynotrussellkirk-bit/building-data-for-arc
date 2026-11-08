# 37cec5981f3a

0-bg grid (h, w~7-10) with: (a) cell (0, 0) holds CONTROL in {1, 2}; (b) 3 SOURCE CELLS in DISTINCT non-{0, control} colors at hardcoded positions depending on control: ctrl=1 (LR mirror) → sources at (1, 1), (2, 2), (h-2, 1); ctrl=2 (UD mirror) → sources at (1, 2), (1, w-3), (2, 1). Some sources may have a 2-cell stripe extension. Rule (MIRROR SOURCE CELLS BY CONTROL AXIS): READ control at (0, 0). For EACH non-{0, control} SOURCE CELL at (r, c): ctrl=1 → PAINT (r, w-1-c) with the same color (left-right mirror); ctrl=2 → PAINT (h-1-r, c) with the same color (up-down mirror). The control + originals stay. Net: source cells mirror across the axis selected by control.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
