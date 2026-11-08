# Solve work log

I had not opened this task's generator, Racket rule, private labels, prior solve
notes, or any assigned-generator source. I used only the visible examples emitted
by `python3 solve_episode.py blind prepare` and small Python component analyses of
`solve-blind/challenge.json`.

## Observations and rejected hypotheses

At first the outputs looked shape-driven because several examples contain repeated
polyominoes. I segmented each color into 4-connected components and compared shape,
size, color multiplicity, adjacency, and position. Shape-frequency explanations
failed: in the second example only one of three congruent L pentominoes changes,
and in the third example only one of two congruent skew pentominoes changes.

The decisive positional feature was border contact:

- Example 0 changes exactly the object touching the top edge, the object touching
  the left edge, and the object touching the bottom edge.
- Example 1 changes exactly two left-edge objects and one bottom-edge object.
- Example 2 is especially diagnostic because color 5 has two separate components;
  only its top-edge component changes, while the interior component stays color 5.

No unchanged component touches an edge, and every changed component does. Diagonal
contact is not enough to merge objects; same-colored objects are segmented with
4-neighbor connectivity.

## Implemented hypothesis

Copy the grid. For every 4-connected nonzero monochromatic component, recolor all
of its cells to 7 iff at least one component cell lies on row 0, the last row,
column 0, or the last column. Leave background and interior objects unchanged.

For the visible queries this predicts:

- Query 0: recolor the right-edge color-8 object and the bottom-edge lower color-1
  object; preserve the interior color-5, color-4, and upper color-1 objects.
- Query 1: recolor the right-edge color-8 object and the bottom-edge lower color-4
  object; preserve the interior upper color-4 and color-2 objects.

Remaining uncertainty is low and is limited to the standard ARC convention that
objects are 4-connected monochromatic components, which is directly supported by
example 2.
