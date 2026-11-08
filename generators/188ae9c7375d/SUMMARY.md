# 188ae9c7375d

0-bg grid (h×w, ~6-13 by ~8-16) containing 1-5 connected components per color in {2 (red), 3 (green), 4 (yellow)}. All components are 8-conn isolated (≥1-cell buffer). Some distractor cells in other non-{0,2,3,4} colors may be scattered (rule ignores them). At least one of n2, n3, n4 differs (so output isn't uniform). Rule: count connected components of color 2 (call it n2), color 3 (n3), color 4 (n4). Build 3 × max(n2, n3, n4) output. Row 0 has color 2 in the first n2 cells (rest 0); row 1 has color 3 in first n3 cells; row 2 has color 4 in first n4 cells. Bar chart with row colors 2, 3, 4.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
