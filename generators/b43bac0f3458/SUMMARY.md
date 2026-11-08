# b43bac0f3458

3 isolated small shapes (each ≤3×3 bbox) in distinct non-bg colors. Rule: for each shape, compute bbox edge-cell counts (cells on each of top/bottom/left/right side of bbox). If shape's bbox height < 3, anchor toward the side with more cells. Compose all 3 into a single 3×3 output, overlaid by position score order.

Kind: `per_puzzle`. Imported version: `1.3.3`.
Approval is derived by the catalog from current code and retained evidence.
