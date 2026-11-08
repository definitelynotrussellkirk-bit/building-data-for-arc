# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — marker behavior depends on rectangle color

I inspected only the four visible training pairs and the two visible query inputs.
The non-background shapes are solid axis-aligned rectangles of color 5 or 6, and
every color-9 cell is immediately orthogonally adjacent to one rectangle side.

Hypothesis:

- For a color-5 rectangle, erase the whole rectangle, retain the outside 9, and
  copy that 9 one step onto the touched boundary cell.
- For a color-6 rectangle, retain the rectangle, erase the outside 9, and move
  the 9 inward along the same row/column to the central depth.  For odd
  thickness this is the unique middle cell; for even thickness the examples
  choose the farther of the two middle cells, equivalently `thickness // 2 + 1`
  steps from the outside marker.

Evidence/probes: I enumerated each solid 5/6 component and compared input/output
9 coordinates.  This accounts for every marker in all four examples, including
1-cell-thick, 3-cell, 4-cell, and 5-cell traversal depths.  It also explains why
5-objects leave two adjacent 9 cells (outside plus boundary) while 6-objects
leave only the moved interior 9.

Implementation: label connected 5/6 components from the untouched input, erase
all 5-components, then apply marker actions based on their original adjacent
component.  Unrelated 9 cells are conservatively left unchanged.  Remaining
uncertainty is whether unseen data can place one marker adjacent to multiple
objects; the visible construction never does.
