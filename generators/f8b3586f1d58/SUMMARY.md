# f8b3586f1d58

0-bg grid (h~6-10, w~7-11) with 3-6 ISOLATED COLORED CELLS in distinct non-bg colors placed at positions in the LEFT HALF (columns 0..(w-1)//2). The right half is initially empty. Rule: compute the VERTICAL CENTER LINE at column (w-1)/2. For every non-zero cell at (r, c) in the left half, MIRROR it across the center line — paint a copy at (r, w-1-c) preserving its color. The original left cells stay in place. Cells exactly on the centerline mirror to themselves (no-op). Net: every left-half colored cell gets a mirror twin on the right; the grid becomes horizontally symmetric.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
