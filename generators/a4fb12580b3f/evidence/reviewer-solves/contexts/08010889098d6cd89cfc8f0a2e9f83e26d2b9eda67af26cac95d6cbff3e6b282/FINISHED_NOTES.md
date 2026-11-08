# Solve work log

## Exposure

Before this solve I had not opened the task generator, canonical rule, reference
solutions, private labels, prior solve explanations, or review records for task
`a4fb12580b3f`. I used only the public examples printed by `blind prepare` and
the generated challenge files.

## Revision 1 — orthogonal contact selects whole components

Hypothesis: color 1 is a marker object. For each other nonzero color, split its
cells into 4-connected same-color components. If any cell of a component is
orthogonally adjacent to a color-1 cell, recolor the entire component to color
4. Leave the marker, background, and all non-touching components unchanged.

Evidence from the visible examples:

- Example 0 has three distinct components touching the marker: a lower color-6
  triomino, a color-3 domino, and a color-5 domino. All are recolored. Same-color
  components elsewhere remain unchanged. The upper and lower color-6 triominoes
  are only diagonally related, so 4-connectivity is required.
- Example 1 recolors a one-cell color-6 component and a color-3 component that
  touch the marker. A pre-existing color-4 component also touches it and remains
  color 4. Distant components of colors 3, 6, and 7 remain unchanged.
- Example 2 recolors the touching components of colors 3, 5, and 9, while
  preserving distant components of those colors and a distant color-4 object.

Rejected alternatives:

- Recolor only the cells directly adjacent to the marker: contradicted because
  whole multi-cell components change.
- Use diagonal contact: contradicted by same-color components that are diagonal
  to one another but only the orthogonally marker-adjacent component changes.
- Recolor every occurrence of a selected color: contradicted by distant
  components of the same colors remaining unchanged.

Implementation: breadth-first search over same-color 4-connected components,
record whether each component touches any color-1 cell, then recolor that full
component to 4. Remaining uncertainty is limited to unseen malformed cases such
as ragged grids; all provided ARC grids are rectangular.
