# ff4dfc92ad29

Large 0-bg grid with N (3-4) connected components of varied thicknesses. Each component is a solid RECTANGLE (shorter side 2d-1 or 2d -> distinct onion depths d=1..N) in its own color from {1..8}; an optional color-9 square is a decoy the rule ignores. Rule: for each component, compute max onion depth (how many concentric layers peel away). Sort components by (depth ascending, color ascending). Output is 1×N grid of the colors in sorted order.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
