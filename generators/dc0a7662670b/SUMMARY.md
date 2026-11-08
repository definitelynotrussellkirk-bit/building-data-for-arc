# dc0a7662670b

Find each nonzero same-color 4-connected component, compute its true exposed
4-neighbor edge perimeter, sort components by perimeter descending with
ascending color as the tie-break, crop each component, and stack the crops
vertically with one blank row between them.

Version `2.0.0` uses a deterministic four-profile lesson schedule:

- `canonical_four` matches the canonical 4-object size/palette regime;
- `bbox_tie` separates true perimeter from bounding-box perimeter;
- `area_inversion` refutes the cell-count shortcut that fits every canonical pair;
- `color_tie` teaches the ascending-color tie-break absent from canonical pairs.

Every four consecutive ordinary samples contain all four profiles. Exact height,
width, and profile overrides are validated and observable. The canonical Racket
rule remains unchanged and is pinned by `RULE_HASH = eff15ddf94a7`.

Kind: `per_puzzle`. Reviewed version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
