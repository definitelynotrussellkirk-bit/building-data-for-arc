# a86a630485ac

On a 0-background grid, treat each nonzero monochrome 4-connected component as
an object. Normalize each object to its bounding box and keep it in place exactly
when its occupied cells are invariant under left-right reflection; erase every
other object. Exact canonical anchors remain on every fifth sample. Every
ordinary lesson includes an LR-only kept object and a UD-only erased object with
identical cell count and bounding-box dimensions; the schedule alternates 3x3
and connected 3x4 pairs so prototype, size, aspect-ratio, position, and
horizontal-symmetry shortcuts fail.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
