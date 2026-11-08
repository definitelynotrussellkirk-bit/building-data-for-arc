# aae737932036

0-bg grid (h, w ∈ 8-13, by difficulty) with: (a) BOTTOM ROW (row h-1) ENTIRELY filled with COLOR-1 (FLOOR); (b) N_WALLS ∈ 0-5 additional COLOR-1 cells placed at random interior positions (rows 2..h-3) acting as walls/floors splitting columns; (c) N_MARKERS ∈ 2-10 scattered NON-1 COLORED MARKERS (colors 2..9) placed at random non-1 positions in rows 0..h-2. Rule (COLUMN GRAVITY: FOR EACH COLUMN, NON-1 SEGMENTS BETWEEN ADJACENT 1-CELLS COLLECT THEIR NON-0 NON-1 MARKERS AND PACK THEM AT THE BOTTOM OF EACH SEGMENT; 1-CELLS AND THE FLOOR STAY): For EACH column c: SPLIT it into segments separated by COLOR-1 cells (walls + floor). For EACH segment: EXTRACT its non-0 non-1 markers in order; CLEAR the segment to 0; PACK the markers at the BOTTOM of the segment (just above the next 1). Net: every marker falls down its column until it lands on a 1-cell.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
