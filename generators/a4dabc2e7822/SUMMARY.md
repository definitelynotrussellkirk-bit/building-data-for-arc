# a4dabc2e7822

0-bg grid (h~8-10, w~11-14) with: (a) ROW 0 containing 1-4 TRANSFORM CODES (values 1-4) at random distinct columns; (b) ROW 1 entirely 0 (separator); (c) ROWS 2..h-1 contain a SMALL BASE MOTIF (3-5 cells, 4-conn) in a DISTINCT color (8 or 9). Rule (PACK TRANSFORMED CROPS BY ROW-0 CODES): identify the BASE MOTIF in rows 2+. CROP its bbox. For EACH TRANSFORM CODE in row 0 (left to right): APPLY the transform (1=identity, 2=rot CW 90°, 3=rot 180°, 4=rot CCW 90°) to the cropped base. PACK the transformed pieces LEFT-TO-RIGHT with ONE BLANK COLUMN between them. Net: motif appears multiple times, transformed per row-0 codes.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
