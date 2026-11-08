# Solve work log

## Exposure declaration before solving

I did not inspect this task's generator, Racket rule, canonical record, reference
solution, private labels, audit evidence, or earlier solution explanations. I did
accidentally read the packet's generic `ARC-DESIGN.md` guidance before the blind
solve was prepared; it contained no task-specific examples or rule information.

## Revision 1 — left-to-right object extraction and vertical packing

Across all five visible demonstrations, every nonzero shape is a separate
monochrome 4-connected object. The output crops each object to its bounding box,
orders the crops by the object's original leftmost column (with top row as a
stable tie-breaker), left-aligns them in a canvas whose width is the widest crop,
and inserts one all-zero row between consecutive objects.

Evidence from the visible examples:

- Example 0 orders the 7, 3, and 4 objects by columns 0, 3, and 7.
- Example 2 shows objects may overlap in horizontal span; the 8 crop at column 1
  still precedes the vertical 6 crop at column 3.
- Example 3 has two objects with the same leftmost column; top-to-bottom order
  matches the output.
- Example 4 confirms disconnected objects of the same color remain separate and
  are ordered by position rather than color.

The implementation uses same-color 4-connectivity, preserves each crop exactly,
pads only on the right, and returns an empty grid if there are no objects. The
main remaining uncertainty is how an unseen case with differently colored cells
sharing an edge should be segmented; the demonstrations only contain monochrome
objects, so same-color connectivity is the least-assumptive interpretation.
