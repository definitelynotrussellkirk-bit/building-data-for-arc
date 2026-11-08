# b04b767a1685

0-bg grid with a single connected motif (3-6 cells) in one non-zero color, surrounded by bg padding. The motif's bbox is strictly smaller than the grid (so the rule's crop produces a smaller output). Rule: find the bbox of all non-zero cells. Output = the subgrid bounded by min/max row and col of non-zero cells. Output dims = (max_r - min_r + 1) × (max_c - min_c + 1).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
