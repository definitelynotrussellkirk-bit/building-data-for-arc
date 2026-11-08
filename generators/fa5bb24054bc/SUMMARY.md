# fa5bb24054bc

A zero-background grid contains 2–6 connected monochrome panels separated by one or two full blank columns. For each panel, compute `(area, enclosed 4-connected holes)`. The output is the symmetric `N×N` relation matrix: `5` on the diagonal, `6` when both features match, `2` for area-only equality, `3` for hole-count-only equality, and `0` otherwise.

Version `3.0.0` uses a constructive four-profile curriculum (`area_only`, `holes_only`, `both`, `unrelated`). Every four consecutive samples expose all four off-diagonal labels, including code `2`, which is absent from the canonical demonstrations. Every seventh sample is a canonical-size anchor; ordinary samples vary panel count, colors, orientations, vertical placement, separator width, and include multi-hole extensions when height permits.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Canonical authority is unchanged and pinned by `RULE_HASH = b6e6c6e2c73c`.
Approval remains catalog-derived; this review does not change training approval.
