# b9784a00e013

0-bg grid (h ∈ 8-10, w ∈ 8-11) with: 4 NON-OVERLAPPING COMPONENTS each in a DISTINCT non-bg color drawn from {1..9}: (a) ONE LARGE 6-CELL component (L-pentomino: (0,0),(0,1),(0,2),(1,0),(1,1),(2,0)) at fixed position (1, 1) in colors[0]; (b) ONE 2-CELL pair at (0, w-3..w-2) in colors[1]; (c) ONE 3-CELL L-tromino at (h-2..h-1, 0..1) in colors[2]; (d) ONE 2-CELL vertical at (h-2..h-1, w-2) in colors[3]. The 6-cell component is STRICTLY LARGER than any other (unique-largest). Rule (KEEP THE UNIQUE LARGEST CONNECTED COMPONENT, ERASE ALL OTHERS): EXTRACT every 4-connected non-bg component with cell count. FIND the component with MAXIMUM cell count (unique). PRODUCE a fresh same-size grid of 0s. PAINT only the largest component's cells in its original color. ALL OTHER components erased to bg. Net: noisy multi-component input becomes a clean single-component output.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
