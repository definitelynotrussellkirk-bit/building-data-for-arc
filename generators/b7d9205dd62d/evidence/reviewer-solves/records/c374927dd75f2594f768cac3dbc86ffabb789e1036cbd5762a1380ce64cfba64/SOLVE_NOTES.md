# Blind solve notes

## Exposure declaration

I inspected only `solve-blind/challenge.json` before implementing the solver.
I have no earlier exposure to this task's solution and have not consulted a
reference implementation, generator, canonical rule, task notes, private labels,
or other repository files. Subsequent inspection is limited to my own newly
created blind-solve files and outputs of supported solve commands.

## Visible observations and hypothesis

- Each nonzero color in the visible examples appears at two input positions.
- When those positions differ in both row and column, the output fills their
  inclusive axis-aligned bounding rectangle with that color.
- A pair sharing one column (color 4 in training example 2) or one row (color 8
  in training example 3) remains unchanged, including the zeros between markers.
- The examples do not establish behavior for overlapping rectangles or more
  than two markers of one color.

## Revision 1

Implemented the rectangle hypothesis in `solution.py`. The solver copies the
input, groups nonzero cells by color, and fills a color's bounding rectangle only
when its extent is positive in both dimensions. For the visible two-marker cases,
this condition selects diagonal pairs and preserves aligned pairs.

No rejected hypotheses, execution failures, or revisions have occurred yet.
The supported visible-example check is the next probe; no private-correctness
claim is made.
