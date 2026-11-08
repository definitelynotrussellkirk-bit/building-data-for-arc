# 12b35b7402b6

Count every gray (`5`) marker in the top row and recolor the unique blue (`1`)
4-connected component with that many cells red (`2`). The repaired generator
uses only strict, realizable controls and independently varies marker count,
marker span, target rank, object count, grid size, and contiguous/scattered
marker layout.

The native parametric family preserves that rule byte-for-byte as
`mode=canonical`. `mode=linked_payload` composes it with a second stage: after
the selected blue bridge becomes red, recompute red 4-connectivity, take the
unique largest newly merged red component, and recolor the unique azure (`8`)
component of that size yellow (`4`).

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash:
`cb01ed25524c`.
