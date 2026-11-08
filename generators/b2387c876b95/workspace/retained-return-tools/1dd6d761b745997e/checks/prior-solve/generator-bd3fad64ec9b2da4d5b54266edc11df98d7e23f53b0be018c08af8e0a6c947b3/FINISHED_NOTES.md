# Solve work log

This is a human-authored visible-example solve. Before this episode I had already
reviewed the assigned generator and therefore had earlier exposure to the intended
rule. During this episode I did **not** reopen the generator, Racket program,
reference solutions, private labels, or earlier solve notes; I used only the
fresh visible examples printed by `review.py solve prepare`.

## Revision 1 — divider reflection with a distinct output color

Visible observations:

- Every input has exactly one complete gray/color-5 row or column.
- Color 2 is the only object that gains cells in the output.
- Each added cell is color 3 and lies at the equal-distance mirror coordinate
  across the full color-5 divider.
- The original color-2 source, divider, background, and unrelated colors
  (4/6/7/8/9 in the examples) stay unchanged.
- The examples cover vertical and horizontal dividers and source objects on both
  sides, so a fixed “copy right/down” rule is ruled out.
- Examples 0 and 3 use three-cell L shapes while examples 1 and 2 use four-cell
  L/J shapes, so the transformation is cellwise rather than template-specific.

Implemented formula:

- vertical divider at column `d`: each color-2 `(r,c)` paints color 3 at
  `(r, 2*d-c)`;
- horizontal divider at row `d`: each color-2 `(r,c)` paints color 3 at
  `(2*d-r, c)`.

The implementation preserves the input and changes only the legal reflected
positions. Remaining uncertainty is low because all four visible demonstrations
exercise the same formula with both orientations and both source directions.
