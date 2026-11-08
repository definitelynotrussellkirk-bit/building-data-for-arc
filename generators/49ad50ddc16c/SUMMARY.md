# 49ad50ddc16c

Grid with color-5 walls scattered as singletons or short segments. Within each column, segments between consecutive walls (or wall and grid edge) hold scattered non-zero non-5 colored cells. Rule: for each column, scan top-down. Walls (5) preserved in place. Within each segment between walls, collect all non-zero non-5 values in top-to-bottom order and pack them at the BOTTOM of the segment, with 0 padding above. Equivalent to per-column gravity-down within wall-bounded segments.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
