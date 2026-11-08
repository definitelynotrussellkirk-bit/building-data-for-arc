# Solve work log

I had not seen task `6c93e8516229`, its generator, its canonical rule, or a prior
solution before this blind solve. I used only the visible challenge grids and a
small local script that split gray cells into 4-connected components and printed
component degree counts and normalized shapes.

## Revision 1 — shape-graph classification

Hypothesis: recolor each gray component independently. The visible outputs split
objects into three classes:

- color 2: every object has a degree-3 junction (a T-like tree);
- color 6: every object is a simple path with exactly two 90-degree direction
  changes;
- color 1: the remaining shown objects, including straight paths, one-turn and
  three-turn paths, and the degree-4 plus.

The query objects repeat these witnessed classes: T objects, U/C/two-turn paths,
and the remaining path/plus shapes. I implemented 4-connected component finding,
explicit path traversal for turn counting, and the classification above. A
possible alternative is that the task names a finite set of glyph families, but
the graph/turn rule is the simplest invariant shared by every visible example.
Remaining uncertainty is behavior on cycles or more complicated branched trees,
which do not appear in the visible lesson; the fallback places them in color 1.
