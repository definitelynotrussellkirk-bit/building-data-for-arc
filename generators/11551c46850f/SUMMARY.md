# 11551c46850f

Grid with VERTICAL color-5 walls (one or more full or partial color-5 columns) dividing the grid into row-segments. Each row-segment between consecutive walls (or wall and grid edge) holds some scattered non-zero non-5 values. Rule: for each row, scan left to right. Preserve color-5 cells in place. Within each segment between walls, collect all non-zero non-5 values in left-to-right order and pack them at the LEFT of the segment, filling the remainder with 0. Equivalent to per-row gravity-left within wall segments.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
