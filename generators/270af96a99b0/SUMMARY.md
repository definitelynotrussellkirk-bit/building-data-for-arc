# 270af96a99b0

A zero-background grid contains exactly four isolated, distinctly colored objects. Extract each same-color 4-connected object, crop it to its tight bounding box, compute its **true exposed-edge perimeter**, and sort by `(perimeter, source top row, source left column)` ascending. Pack the normalized crops left-to-right with one zero separator column and top-align them; keep background holes inside each crop.

The generator uses three scheduled profiles with decisive perimeter ties at 8, 10, and 12. Every profile rebuts source order, area order, bounding-box perimeter, color order, descending perimeter, bottom alignment, no-gap packing, and filled-bbox shortcuts. Periodic 8×9, 8×10, and 8×11 anchors preserve all canonical size/palette profiles, and every generated transformation remains in the canonical shrink relation.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `cf57cf408f13`.
Approval is derived by the catalog from current code and retained evidence.
