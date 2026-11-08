# e873f4e123b6

0-bg grid with several sparse non-bg cells (random colors 1-9) anywhere, INCLUDING the bottom row and some vertically stacked. Rule: SIMULTANEOUSLY (on input state) each non-zero cell at (r,c) drops to (r+1,c) iff (r+1,c) is in-bounds AND 0 in the input; cells at the bottom row or with a non-zero cell directly below STAY. Both branches (drop / stay) are exercised every instance; positions, colors, counts and grid size vary.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
