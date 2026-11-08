# ebff81ea3252

An 8–11 by 9–11 zero-background grid contains one to three green cardinal
crosses and one separate five-cell green non-cross decoy. A target cross is
either an isolated five-cell plus or has one additional connected corner cell.
The rule scans the original input for an interior color-3 center whose north,
south, west, and east neighbors are also color 3, then recolors exactly those
five cells to color 7. Attached cells and non-cross components remain green.

Default sample indices alternate isolated and attached contexts and cycle target
counts 1, 2, 3, so every three-example lesson contains evidence against treating
a target as an isolated five-cell component. Exact overrides are available for
`grid_h`, `grid_w`, `n_pluses`, and `context_mode`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`deb3ac96cc89`.
