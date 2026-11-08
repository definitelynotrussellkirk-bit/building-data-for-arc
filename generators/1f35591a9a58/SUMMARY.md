# 1f35591a9a58

0-bg grid with EXACTLY 2 connected components in distinct non-zero colors. The two components have OVERLAPPING bounding boxes — intersection region of width ≥1 and height ≥1. Components may touch or be intertwined (e.g., L-shapes that fit together). Rule: find both objects (sorted by color). Compute the bbox intersection rectangle (max of r1s, min of r2s, max of c1s, min of c2s). Output a fresh canvas with that rectangle painted color 8. Component cells in the input are NOT preserved in output.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
