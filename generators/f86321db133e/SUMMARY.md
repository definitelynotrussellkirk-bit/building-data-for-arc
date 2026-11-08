# f86321db133e

0-bg grid (size varies) with 2-7 SCATTERED connected MOTIFS, each a random polyomino (3-8 cells) in a DISTINCT non-bg color, placed at non-overlapping isolated positions. Rule: extract every 4-connected non-bg component, crop each to its bbox, SORT by (cell-count DESC, then color ASC), and PACK the crops LEFT-TO-RIGHT, TOP-ALIGNED, with a 1-column gap between them. Output height = max motif height, width = sum of motif widths + (n-1) gaps. Net: scattered colored motifs collected into a horizontal gallery, biggest first.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
