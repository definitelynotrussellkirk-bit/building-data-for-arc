# 694386b5a151

0-bg grid (h×w, ~9-13 by ~11-16) with: (a) a 'WINNING FAMILY' of 2-4 connected components that SHARE the same normalized shape (e.g., all L-shaped, all 2×2 squares), each in a DIFFERENT non-zero color; (b) 1-2 'distractor' components in OTHER normalized shapes (and distinct colors). All components are 8-conn isolated. The winning family is strictly larger than any other family. Rule: group components by normalized shape. Pick the family with the MOST members. Sort the family by bbox top-left (row asc, col asc). Pack them horizontally with 1-cell gaps. Output height = max bbox height of family members. Each member's color is preserved in its slot.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
