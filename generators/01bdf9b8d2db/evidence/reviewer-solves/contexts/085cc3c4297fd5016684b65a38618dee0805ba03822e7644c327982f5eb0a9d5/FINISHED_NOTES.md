# Solve work log

## Prior exposure

Before this blind episode I had not opened the task's generator, Racket rule,
reference solutions, private query labels, audit records, or earlier solution
explanations. I used only the public examples emitted by `blind prepare` and the
prepared `challenge.json`.

## Revision 1 — connected chambers bounded by color 5

**Observation.** Color 5 forms walls. In each 4-connected region of cells that
are not 5, the input contains zeros plus one nonzero seed color. The output keeps
the walls and replaces every cell in that region with the seed color.

The irregular upper-right region in training example 1 is the key probe: rows 1–2
connect to row 4 only through column 8 because row 3 columns 6–7 are walls. Its
seed 3 nevertheless fills the entire bent 4-connected chamber. This rules out a
simple rectangular bounding-box fill and supports component flood fill.

**Implementation.** Traverse every non-5 component with four-neighbor BFS,
collect its nonzero/non-5 seed colors, and fill it when there is exactly one
distinct seed. Components with no seed or conflicting seeds are left unchanged,
since the visible examples do not establish behavior for them.

**Alternatives considered.** Filling each rectangular wall-delimited box is too
weak for the bent chamber above. Expanding independently from each colored pixel
until a wall is equivalent on the demonstrated inputs, but component-first logic
states the inferred object more directly and avoids order dependence.

**Remaining uncertainty.** The examples consistently use 0 as chamber background
and 5 as the wall color, with one distinct seed per component. I have no visible
evidence for malformed chambers or a different wall color, so I do not generalize
those cases.
