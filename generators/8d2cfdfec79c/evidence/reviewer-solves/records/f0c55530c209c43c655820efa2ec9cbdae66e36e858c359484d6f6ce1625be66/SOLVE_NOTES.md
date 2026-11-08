# Solve work log

## Exposure

Before this solve I had not opened this task's generator, Racket rule, canonical
record, prior solutions, audit evidence, or private query labels. I used only the
visible examples emitted by `python3 review.py blind prepare` and
`solve-blind/challenge.json`.

## Revision 1 — paired corners become rectangle borders

Each nonzero color occurs exactly twice. In every visible example the two cells
act as opposite corners of an axis-aligned bounding rectangle, and the output
fills that rectangle's perimeter with the same color. A two-row or two-column
rectangle therefore becomes solid, as shown by color 6 in train example 2 and
color 5 in train example 1.

The overlapping top borders in train examples 0 and 2 reveal precedence. Colors
are encountered row-major; drawing rectangle perimeters in first-occurrence
order makes the later first-seen color overwrite earlier borders. This explains
why 7 covers 5 on train example 0's shared top edge and row 7 intersections, and
why 9 covers 5 on train example 2's shared top edge.

I first wrote a visible-example test harness outside the packet workspace. It
failed on the supplied `NotImplementedError`, confirming the test exercised the
missing solver. I then implemented the minimal rule: gather nonzero coordinates
in insertion order, compute each color's bounding box, and draw its four sides
onto an initially zero grid.

Remaining uncertainty: all visible colors have exactly two cells, so behavior
for malformed counts is intentionally unspecified. The overlap-order inference
is supported by two examples but private queries remain masked.
