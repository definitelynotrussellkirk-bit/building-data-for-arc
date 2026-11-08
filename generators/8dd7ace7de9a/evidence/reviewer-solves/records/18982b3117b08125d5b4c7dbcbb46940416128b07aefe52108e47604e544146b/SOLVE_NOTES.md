# Post-repair solve work log

This is a human reasoning log based on `solve/challenge.json` only during the solve phase. I had already seen the selected rule while reviewing the generator, so this is an exposed solve and I will declare earlier exposure as `yes`.

## Revision 1

**Observed pattern.** In every visible example, color 6 behaves as corruption rather than part of the answer. The remaining cells repeat a small rectangular tile. Example 1 repeats every 3 rows and 3 columns; example 2 every 2 rows and 2 columns; example 3 every 4 rows and 3 columns.

**Hypothesis.** Ignore color 6 while testing candidate row/column periods. Search candidate periods from smallest upward. A candidate is valid when all non-6 cells assigned to the same tile residue agree and every residue has at least one known representative. Reconstruct the full grid from the first valid tile.

**Alternatives rejected.** Local majority or nearest-neighbor filling can repair many 6 cells but does not explain the exact long-range repeated placements. Treating 6 as ordinary data contradicts every output. Fixed square periods fail the third example, whose visible pattern is 4 by 3.

**Implementation.** `solution.py` performs a lexicographic search over row periods and column periods up to half the grid dimensions, then fills every cell from the recovered tile. If no complete period exists, it returns an all-zero grid rather than inventing unresolved colors.
