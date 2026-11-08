# Solve work log

Earlier exposure before this solve: none known. I did not inspect any generator,
reference rule, private answer, previous solution, or audit evidence.

## Revision 1 — periodic-tile restoration

**Hypothesis.** Each grid is a small two-dimensional color tile repeated across
rows and columns. Color 0 marks erased cells, and the output restores those cells
from the repeated pattern. The examples use a 2×3 or 3×2 base tile, but the
implementation should infer rather than hard-code either orientation.

**Evidence from visible examples.** In train 0 and train 2, rows alternate and
columns repeat every three positions; the intact copies uniquely supply every
zero. In train 1, rows repeat every three and columns every two. Replacing zeros
with the color at the same row/column residue exactly reproduces all three visible
outputs. The two queries exhibit the same two orientations.

**Program.** Search all row/column periods. Ignore zeros while checking whether
all observed cells in each residue class agree. Require every cell of the inferred
base tile to be represented by at least one nonzero observation, then select the
smallest-area consistent tile and render it over the full grid.

**Alternatives considered.** Copying the nearest complete row would work on some
examples but is orientation-specific and fails when corruption spans several row
types. Per-row sequence completion also misses the vertical repetition. The joint
residue-class formulation captures both.

**Remaining uncertainty.** The visible data strongly supports zero-as-erasure and
smallest periodic tile. A different hidden convention could matter only if a query
contains an intentional zero in the tile or if two equally small periodic models
fit all observations; neither is suggested by the examples.
