# 2d8e81383796

0-bg grid with N (2-5) connected non-bg components, each in its own distinct color. Rule: for each component, compute its max-col-peak (max over columns of the count of cells the component occupies in that column) — equivalently, the longest vertical run within the component's footprint. Pick the component with the STRICTLY LARGEST max-col-peak (ties broken by size, then top-left). Output is that component's bbox crop, recolored so non-bg cells become 8 (bbox holes stay 0).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
