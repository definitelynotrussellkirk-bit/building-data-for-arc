# 3a96552d8c7c

For each row independently, fill the cells strictly between two nonadjacent color-5 endpoints with color 3 only when the row contains exactly two 5s and the entire interior is 0. All other rows remain unchanged.

The version-2 curriculum uses a deterministic three-profile schedule. Every ordinary three-example window contains the minimum legal `5 0 5` boundary plus counterexamples to four plausible shortcuts: requiring two interior zeros, ignoring blockers, accepting three-or-more 5s, and applying the rule to any repeated color. Canonical-size profiles rotate through `6x8`, `7x9`, and `8x10` in every difficulty band.

Exact observable controls are `grid_h`, `grid_w`, `n_fill_rows`, `span_style`, and `negative_mode`. The reusable source-only qualification command is documented in `workspace/README.md`; the repository battery remains the authority for Racket parity.

Kind: `per_puzzle`. Version: `2.0.0`. Rule hash: `91ba1164c014`.
Approval is derived by the catalog from current code and retained evidence.
