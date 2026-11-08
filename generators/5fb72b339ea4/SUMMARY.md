# 5fb72b339ea4

Fixed 5×5 grid with FOUR 2×2 CORNER PATCHES at (0..1, 0..1), (0..1, 3..4), (3..4, 0..1), (3..4, 3..4). Three patches are IDENTICAL (the 'common' patch) and exactly ONE is different (the 'unique' patch). The middle row, middle column, and center cell may contain decoy values (ignored by the rule). Rule: extract the 4 corner 2×2 subgrids; for each, count how many of the 4 are equal to it; the UNIQUE one is the patch with count exactly 1. Output: that 2×2 unique patch.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
