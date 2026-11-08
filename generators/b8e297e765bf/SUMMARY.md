# b8e297e765bf

EVEN-DIM grid (h, w~12-18, both even) split into 4 QUADRANTS (TL/TR/BL/BR). Each QUADRANT filled with one of 4 DISTINCT BASE COLORS from a palette (warm/cool/broad/primary, excluding noise color). Each quadrant has scattered NOISE (COLOR-4 by default) cells: 7-10 noise cells in the WINNING quadrant, 1-3 in the others. EXACTLY ONE quadrant has the highest noise count (unambiguous winner). Output uniq_out=8 (intrinsic — output is a 1×1 grid of the winning quadrant's color, with ~8 palette × few winner colors). Rule (EMIT 1×1 OF MOST-NOISY QUADRANT's COLOR): For EACH non-zero, non-noise color C in the grid: COUNT noise cells in C's filled region. Pick the C with MAX noise count. EMIT a 1×1 grid of color C. Net: most-noisy quadrant's color wins; output is a single cell.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
