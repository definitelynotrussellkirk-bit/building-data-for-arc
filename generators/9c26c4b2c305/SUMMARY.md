# 9c26c4b2c305

Split the 9-row input at its solid middle row into aligned 4-row top and bottom
panels. For every aligned cell, output green (3) when either panel cell is
nonzero; output black (0) only when both cells are black.

Kind: `per_puzzle`. Reviewed version: `3.1.0`.

Version 3.1.0 adds an equal-panel-color lesson profile and an executable
canonical-fitting rival, `same_color_xor_otherwise_or`. Every scheduled
four-example lesson now contains an equal-color counterexample while retaining
canonical palette/width support, shifted colors, noncanonical widths, and all
four occupancy relations. The Racket rule is semantically unchanged; the active
base `target_code` was synchronized byte-for-byte to the canonical program.

Final generator SHA-256:
`8ffed236db06f9606aa5f45c3642e406f9e6293b1b8d678df73db2c318ed1e45`.
Approval is derived by the catalog from current code and retained evidence.
