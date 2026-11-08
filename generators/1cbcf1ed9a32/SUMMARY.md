# 1cbcf1ed9a32

Split the input at the two full-height gray (`5`) dividers. In each of the
three equal-width panels, select the unique largest monochrome 4-connected
object and canonicalize its shape over the eight D4 rotations/reflections.
Exactly two panels share one canonical shape; output that normalized shape in
cyan (`8`).

Version `2.0.0` removes the prior cell-count shortcut by making all three
largest objects equal in size, expands the output bank to all free polyomino
classes of 3–7 cells that fit the selected panel, and uses a deterministic
four-slot curriculum that remains identifiable when any one pair in a
five-pair lesson is used as query. Public controls are exact and observable:
`grid_h`, `panel_w`, `common_cells`, `common_pair`, `palette_kind`, and
`secondary_objects`.

The synchronized Racket authority is unchanged and pinned by
`RULE_HASH = dc0d41aa47ba`.

Kind: `per_puzzle`. Generator version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
