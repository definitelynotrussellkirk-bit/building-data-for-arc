# a3342a9df65d

0-bg grid (~6-12 by ~8-16) holding 2-5 ISOLATED 4-connected MOTIFS (random polyominoes of 1-6 cells) in DISTINCT non-0 colors, each separated from the others by >=1 bg cell on all sides so they stay distinct components. Rule (PACK COMPONENTS BY SIZE): extract every 4-connected non-bg component; CROP each to its bbox; SORT by (cell-count DESC, color ASC); PACK the crops left-to-right with one bg column between consecutive crops. Output height = tallest crop; width = sum of crop widths + (n-1). Net: the motifs are lined up largest-first into a compact gallery row, ties broken by color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
