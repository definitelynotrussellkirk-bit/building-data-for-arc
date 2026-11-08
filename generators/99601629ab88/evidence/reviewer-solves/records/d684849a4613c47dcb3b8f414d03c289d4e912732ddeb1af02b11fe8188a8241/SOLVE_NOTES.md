# Solve work log

## Exposure

Before this solve I read only the packet-level start/duties documentation and the
visible challenge prepared by the solve tool. I did not inspect this task's
generator, canonical rule, reference solution, private labels, notes, or audit
evidence.

## Revision 1 — panel lattice mirrored horizontally

The inputs are solid-color rectangular panels separated by complete horizontal
and vertical lines of one divider color. Compressing each panel to its color gives
exactly the output dimensions. In all three demonstrations the output is that
compressed panel matrix with the column order reversed:

- example 0: `[[7,8],[9,8],[7,0],[9,7]]` becomes
  `[[8,7],[8,9],[0,7],[7,9]]`;
- example 1: `[3,2,2,5]` becomes `[5,2,2,3]`, while the all-5 row is unchanged;
- example 2 follows the same left-right reflection.

I first ran a visible-example assertion harness against the untouched template;
it failed at the expected `NotImplementedError`. The implementation now finds a
color that forms both full-width rows and full-height columns, splits the remaining
coordinates into contiguous panel runs, takes each panel's dominant color, and
reverses every compressed row. This avoids assumptions about divider color,
panel dimensions, or lattice dimensions.

Predicted queries from the visible rule:

- query 0: `[[5,0,8,8],[6,8,0,8]]`
- query 1: `[[3,0,5],[3,5,3]]`

Remaining uncertainty: the visible data has a clean one-cell-thick divider lattice
and uniform panels. The code tolerates thicker divider lines and minor panel noise,
but the examples do not establish whether such noise is part of the intended task.
