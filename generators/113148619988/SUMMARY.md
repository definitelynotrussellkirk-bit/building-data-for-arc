# 113148619988

Row 0 holds k color-1 markers (rotation count). Body (rows 1..H-1, cols 0..W-2) has one color-9 anchor + several non-{0,9} colored cells. Rule emits a (H-1) × (W-1) grid: anchor stays at 9, and each colored cell is stamped at every 90° CCW rotation about the anchor for turns = 0..k (k+1 stamps total). Off-bounds stamps drop.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
