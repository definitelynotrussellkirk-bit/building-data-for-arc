# Solve work log

## Exposure before solving

I had not opened the generator, canonical rule, private labels, reference solutions,
or prior solution explanations for task `60c56114260f`. Before preparation I did
read packet-level instructions and the general `ARC-DESIGN.md`; those did not reveal
this task's rule. I used only the visible examples printed by `blind prepare` and the
blind solve files while forming the solution.

## Revision 1 — shape-equivalence matrix

**Hypothesis.** Each nonzero colour is one object. Order the objects by the top-left
cell of their bounding box, then emit an `n × n` matrix. Entry `(i,j)` is colour 8
when objects `i` and `j` have the same occupied-cell shape after translation and a
quarter-turn rotation, and 0 otherwise.

**Evidence from the visible demonstrations.**

- Example 0 has three objects. The two filled 2×2 squares are equivalent and the
  hollow 3×3 frame is not, matching the diagonal plus the 2×2 lower-right block.
- Example 1 has five objects. The three L triominoes are rotations of one another,
  while the two length-3 bars are rotations of one another, matching the two
  equivalence classes in the output.
- Example 2 has five tetrominoes. Only the horizontal and vertical length-4 bars
  are rotationally equivalent, matching the sole off-diagonal pair.

**Implementation.** Collect all coordinates for each nonzero colour, sort colour
objects in reading order by `(minimum row, minimum column)`, canonicalise each set
across its four rotations, and compare signatures pairwise.

**Predicted queries.** Query 0 should group only its horizontal and vertical
length-4 bars; the L, square, and T shapes are singletons. Query 1 should contain
four singleton classes (zig-zag, T, square, and L).

**Remaining uncertainty.** The examples prove invariance under rotation but do not
contain a chiral pair that distinguishes rotation-only equivalence from equivalence
under reflection as well. I chose rotation-only because it is the least additional
invariance supported by the demonstrations. The current query predictions are the
same either way.
