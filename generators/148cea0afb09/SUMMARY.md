# 148cea0afb09

Cell `(0,0)` contains a one-based rank `R`. Clear that marker, find the 2–3 separated 4-connected nonzero objects, sort them by **cell count ascending**, select the `R`-th object, crop it to its tight bounding box while preserving holes as 0, and scale the crop 2× in both dimensions.

The generator uses one component color from 4–9, distinct object cell counts, exact observable axes, and deterministic compact polyomino placement. Every generated sample separates the intended cell-count ordering from the canonical-fitting shortcut “rank by bounding-box area.” Production lessons use 4 demonstrations plus 1 query and declare that rival for semantic checks.

Kind: `per_puzzle`. Generator version: `2.1.0`. Rule hash: `c113614858b9`.
Approval is derived by the catalog from current code and retained evidence; this review does not grant approval or training admission.
