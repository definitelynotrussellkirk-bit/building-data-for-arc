# Visible-only solve notes

## Revision 1

Hypothesis from the three visible demonstrations: color 5 is a wall. Treat every
4-connected non-5 region as one chamber, including a region that reaches the
outer edge through a non-5 border cell. Count nonzero cells, not distinct seed
colors. If and only if the chamber has exactly one nonzero cell, replace all of
its zeros by that cell's color. Empty chambers and chambers with two or more
seed cells remain unchanged.

Checks against the examples:
- Demo 1 leaves the two-color-6-cell chamber unchanged, while filling the
  single-6 and single-7 chambers.
- Demo 2 leaves the two-seed upper-right chamber unchanged and fills the
  edge-open single-1 chamber.
- Demo 3 leaves the upper-left two-seed chamber unchanged and fills the two
  single-seed chambers despite an offset partial wall.

Implementation: independent 4-neighbor flood fill over cells whose value is not
5, followed by the exact one-seed-cell test.
