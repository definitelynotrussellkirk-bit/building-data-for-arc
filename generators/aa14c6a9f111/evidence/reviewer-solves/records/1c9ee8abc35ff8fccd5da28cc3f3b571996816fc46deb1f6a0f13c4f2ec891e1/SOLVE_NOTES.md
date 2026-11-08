# Solve work log

## Exposure record

Before this solve I had not opened the selected generator, this task's generator,
any Racket rule, reference solution, private labels, or earlier solution notes. I
used only the visible examples printed by `review.py blind prepare` and the local
visible-only check command.

## Revision 1 — deliberate RED baseline

The provided template raised `NotImplementedError`. I ran it once as a deliberate
RED check before implementation. It executed with status `error` and passed 0/3
visible examples, confirming that the check would catch a missing solution.

## Hypothesis

For every nonzero color, the input contains marker cells at opposite corners of
an axis-aligned rectangle. The output replaces the sparse markers with the full
perimeter of that color's bounding rectangle, on an otherwise zero grid of the
same shape. A rectangle only one or two cells thick naturally appears filled
because every cell is on its perimeter.

Evidence from the visible examples:

- Train 0 color 5 spans rows 7..11 and columns 6..8 and becomes exactly that
  5-by-3 outline.
- Train 1 color 4 spans rows 0..10 and columns 2..8 and becomes the large outline.
- Train 2 color 8 spans rows 7..9 and columns 5..7 and becomes a 3-by-3 ring.
- The apparent filled blocks for thin rectangles are consistent with the same
  perimeter rule, so no separate fill condition is needed.

## Revision 2 — implementation

I grouped all nonzero cells by color, computed each color's minimum and maximum
row and column, and painted the top, bottom, left, and right sides into a new zero
grid. Using all observed cells rather than assuming exactly two makes the code
stable if duplicate perimeter markers appear, while preserving the inferred law.

Remaining uncertainty: visible examples do not specify how intersecting rectangles
of different colors should be resolved. The generated examples are disjoint; the
implementation uses first-seen color order, so a later color at an intersection
would overwrite an earlier one.
