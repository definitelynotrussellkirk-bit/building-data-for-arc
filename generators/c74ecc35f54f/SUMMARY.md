# c74ecc35f54f

0-bg grid (h~5-8, w~6-9) with EXACTLY FIVE NON-ZERO CELLS placed at fixed positions: (0, 1), (1, w-2), (h//2, 2), (h-2, w//2), (h-1, w-1). Colors are drawn from a palette of 3 distinct non-0 values C0, C1, C2 from {1..9} and assigned: position (0, 1) = C0 (the FIRST color in row-major scan order), positions (1, w-2) and (h-2, w//2) = C1, positions (h//2, 2) and (h-1, w-1) = C2. So C0 appears once and C1, C2 each appear twice — 5 cells total. Rule (COUNT ALL NONZERO CELLS, OUTPUT A ROW REPEATING THE FIRST-SEEN COLOR THAT MANY TIMES): COUNT n = total number of non-zero cells in the input. SCAN row-major to find the FIRST non-zero cell's color C0. PRODUCE a 1-row × n output where every cell holds COLOR C0. Net: input has scattered colors; output is a horizontal bar of length n=count, all in the first-scanned color. Flagged intrinsic-low (uniq_out=9): output is one of 9 possible {color × length=5} bars.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
