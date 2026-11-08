# 44a257e280a5

Grid (h, w~24-30) with a TRANSLATIONAL PERIODIC PATTERN of period (pr, pc) where pr, pc ∈ 2..4, painted from a tile (pr × pc) using one of 6 PATTERNS (rotated/stripe_h/stripe_v/checker/diagonal/block) over a 2-4 color palette drawn from 1..9. The repeating tile fills the entire grid. Then 2-6 RANDOM CELLS are punched as HOLES (set to bg = 0). Rule (PERIOD DETECTION + HOLE FILL): detect the translational period (pr, pc) of the non-bg cells. For EACH BG (0) CELL at (r, c), LOOK UP the periodic value at (r mod pr, c mod pc) of the underlying tile. PAINT the hole with that color. Original non-bg cells stay. Net: every bg hole gets filled by extending the detected periodic tiling.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
