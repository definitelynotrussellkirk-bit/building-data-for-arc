# 323fded12174

Stable-sort complete rows by descending nonzero occupancy while preserving each
row byte-for-byte.

Kind: `per_puzzle`. Repaired generator version: `2.1.0`.

The generator covers all five exact canonical shape/palette profiles, exposes
truthful `profile` and `cell_layout` overrides, and constructively refutes three
canonical-fitting color-frequency shortcuts. The Racket authority is unchanged.
Approval remains derived by the catalog from current code and retained evidence.

The separate `workspace/parametric/` proposal offers `rank_by=occupancy` (exact
canonical source) or `rank_by=anchor_color`: select the unique densest row,
identify its unique nonzero modal color, then stable-sort original whole rows by
that color's count. It teaches stable ties, supports 3–6 demos and 1–4 queries,
and extends the proposed grammar through substantive 30×30 grids. Native reviewer
qualification and owner acceptance are distinct from canonical production approval.
