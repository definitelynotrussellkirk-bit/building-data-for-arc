# Solve work log

## Prior exposure

Before preparing this task I read only packet-level workflow files (`START-HERE.md`,
`WORK/WELCOME.md`, `WORK/ARC-DESIGN.md`, and `WORK/repo/AGENTS.md`). I did not open
this task's generator, Racket rule, task notes, reference solution, private query
labels, or audit evidence. The generic ARC design note did not describe this task.

## Revision 1 — repeated-color corner objects move inward

The visible examples contain one object anchored at each corner on a background of
color 7. Comparing input and output showed:

- A corner object whose color occurs at two or more corners is moved diagonally
  inward.
- A color occurring at only one corner is left unchanged (the color-1 block in
  train 1 and the color-5/color-9 singletons in train 2).
- The displacement equals the object's bounding-box height vertically and width
  horizontally. Thus a singleton moves one cell inward and a 3×3 block moves
  three rows and three columns inward.
- Shape and color are preserved, and the vacated cells become background.

I considered alternatives such as moving all corner objects, moving only equal
shapes, or moving only objects paired across a diagonal. Train 1 rejects all three:
the unique color-1 block stays, while three color-4 objects of different sizes and
corner arrangements move.

The implementation therefore finds 4-connected non-background components, keeps
only components touching one horizontal and one vertical boundary, counts them by
color, and moves each repeated-color corner component inward by its own dimensions.
The background is inferred as the most frequent color.

Expected queries: query 0 moves all four color-2 singletons one cell inward. Query
1 leaves the unique top-right 2×2 color-3 block in place, moves the three color-1
objects inward, and shifts the bottom-right 2×2 color-1 block to rows 18–19 and
columns 18–19.

Remaining uncertainty: the examples use solid square components. The code permits
rectangles and arbitrary connected shapes by shifting rows by bounding-box height
and columns by bounding-box width, which is the most direct generalization of the
observed displacement.
