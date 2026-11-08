# adfbfbdb73c3

0-bg grid with: (a) ROW 0 holding a LEGEND of 3 distinct non-{0, 5} PRIORITY COLORS at columns 1, 2, 3 (left-to-right priority order, leftmost = highest priority); (b) ROWS 2..h-1 forming a 5-WALLED REGION — color-5 (gray) outer FRAME (row 2 = top wall, row h-1 = bottom wall, cols 0 and w-1 = side walls) plus an INTERNAL VERTICAL WALL at col cw+1 that splits the region into 2 CHAMBERS; (c) each chamber holds 1-2 SEED CELLS (single pixels) using colors from the legend. Rule: for EACH CHAMBER independently, find all seeds and determine the SEED COLOR WITH HIGHEST PRIORITY (leftmost legend position). FILL every empty (bg) cell inside that chamber (not the walls, not the seeds) with that highest-priority color. Net: each chamber flood-fills to its dominant seed-priority color; walls and legend stay.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
