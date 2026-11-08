# Solve work log

## Exposure declaration before solving

I had not seen task `dbecc530afd0`, its generator, its Racket rule, its private
labels, or any previous solution. Before the task was drawn I accidentally
printed part of the packet's generic `ARC-DESIGN.md` while reading the packet
instructions. That document contains only general ARC composition guidance and
no task-specific information. I did not consult it again during this solve.

## Revision 1 — rectangle-interior hypothesis

The visible examples contain sparse yellow (`4`) cells. In each example, four
yellow cells that share two rows and two columns form the corners of an
axis-aligned rectangle. The output colors every cell strictly inside each such
rectangle red (`2`). Unrelated yellow cells are distractors. When two rectangles
overlap, the output is the union of their interiors; a yellow cell belonging to
one rectangle can become red when it lies strictly inside another rectangle.

Checks against the demonstrations:

- Train 1 has corners at rows 1 and 9, columns 0 and 6, producing the 7×5 red
  interior and leaving the unrelated yellow cell at `(8, 9)` unchanged.
- Train 2 has two rectangles: rows 0/4 with columns 6/9, and rows 1/6 with
  columns 0/5. Their strict interiors contain 6 and 16 cells, matching the 22
  red cells in the output.
- Train 0 has overlapping rectangle interiors. Their union has 14 cells and
  explains why the yellow cell at `(5, 4)` is overwritten by red: it is a corner
  of one rectangle but lies inside the other.

Implementation: collect the columns containing `4` in every row. For each pair
of rows, every pair of columns in their intersection defines a rectangle; write
`2` into all strict interior cells of a copied grid. This handles multiple and
overlapping rectangles without relying on a fixed size or count.

Remaining uncertainty: the examples do not show nonzero colors other than `4`,
but the least-destructive interpretation is to copy the grid and overwrite only
rectangle interiors with `2`.
