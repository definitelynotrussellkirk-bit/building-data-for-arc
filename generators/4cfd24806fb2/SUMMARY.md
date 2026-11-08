# 4cfd24806fb2

A unique full-height gray (`5`) column is the reflection axis. Preserve the input and copy every nonzero, non-gray cell left of the divider to the same row at column `2*divider-column`, preserving color. Unrelated cells already on the right remain unchanged.

Version `2.0.0` teaches the rule with a deterministic four-profile schedule:

1. `canonical_sparse` — exact canonical dimension/palette/source-count anchors;
2. `off_center_cluster` — the gray divider, not the canvas midpoint, is causal;
3. `edge_row_motif` — connected, same-row, edge, color-9, and >6-source cases;
4. `preserved_right_noise` — unrelated right-side cells must survive unchanged.

Every four consecutive samples at one seed contain all four profiles. The authoritative Racket rule is unchanged and pinned by `RULE_HASH = b5a5db408e2f`.

Kind: `per_puzzle`. Generator version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
