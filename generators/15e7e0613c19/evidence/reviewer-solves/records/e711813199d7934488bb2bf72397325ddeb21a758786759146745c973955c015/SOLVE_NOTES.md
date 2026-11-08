# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private labels,
or earlier solve notes. I used only the visible examples produced by `blind prepare`.

## Revision 1 — extract, sort, and pack connected objects

Hypothesis: every nonzero 4-connected component is an independent object. Normalize each
object to its bounding box, order objects from smaller to larger (cell count, then bounding
box height and width, then color as a deterministic tie-break), top-align them, and place
one zero column between adjacent objects.

Evidence from the examples:

- examples 0 and 3 order a 1-cell object, a 4-cell object, and a 5-cell object;
- examples 1 and 4 have equal-area objects and order the 2×2 object, the height-2 wider
  object, then the height-4 line;
- example 2 shows that disconnected same-color dominoes remain separate objects and,
  for equal 2×1 objects, colors appear in increasing order;
- output height is the tallest object and output width is the sum of object widths plus
  one separator column per gap.

Remaining uncertainty: the visible data do not distinguish area-first from height-first
ordering because those keys agree on every non-tied example. Both test queries also agree
under either interpretation. I chose area-first because the examples most directly support
"small to large," with shape dimensions and color used only to resolve ties.
