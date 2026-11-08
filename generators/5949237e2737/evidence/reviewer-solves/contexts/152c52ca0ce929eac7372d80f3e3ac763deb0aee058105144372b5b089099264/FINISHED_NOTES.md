# Solve notes: 5949237e2737

This is a human visible-example work log. I had earlier exposure to the task rule
while reviewing its generator, so this is not a blind solve; during this solve
phase I read only `solve/challenge.json` and did not consult the generator,
Racket authority, reference solution, or private labels.

## Revision 1

Every input has a full-height vertical bar of color 8. It divides equal-width
left and right regions. For each nonzero cell left of the bar, compare the cell
at the horizontally reflected coordinate on the same row:

- when the reflected cell has the identical nonzero color, retain that value at
  the reflected right-side coordinate;
- otherwise erase it;
- erase the divider and every unrelated cell.

The five visible outputs distinguish exact position-and-color equality from
occupancy-only, global color-presence, copying the right side, and mirroring all
left cells. I implemented this direct comparison without task-specific sizes or
palettes.
