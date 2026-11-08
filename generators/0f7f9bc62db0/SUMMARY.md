# 0f7f9bc62db0

0-bg grid with: (a) exactly ONE gray(5) cell — the marker; (b) one TARGET non-gray object (some shape, 4-9 cells, in a single color) placed adjacent to the marker (Chebyshev distance ≤ 1 from at least one target cell); (c) 1-4 DISTRACTOR non-gray objects elsewhere (other colors or same target color allowed), NOT adjacent to the marker. Rule: remove the gray cell, find the 8-connected object adjacent to the marker's position, crop to its bbox. The output is just the target's bbox subgrid (no marker, no distractors).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
