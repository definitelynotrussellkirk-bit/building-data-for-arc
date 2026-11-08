# Solve work log

This is a human-authored work log. I had already reviewed the task's generator
and rule before this fresh solve, so earlier rule exposure is **yes**. During the
solve phase I read only `solve/challenge.json` and my own Python files; I did not
consult the Racket rule, generator implementation, reference solutions, prior
solve package, or private query labels.

## Visible-example hypothesis

The five demonstrations consistently treat each monochromatic orthogonally
connected region as a separate object. Objects are ordered by their leftmost
column, with top row breaking equal-left ties. Each object's complete input
bounding rectangle is copied, including a differently colored cell when it lies
inside that rectangle. The rectangles are stacked vertically with one all-zero
separator row. Their common output width is the widest rectangle, and narrower
rectangles use floor-left centering.

## Revision history

1. The generated `NotImplementedError` stub failed immediately in
   `checks/round2/solve-unit-red.log`; this was a local harness check, not a
   submitted solve revision.
2. Implemented the single hypothesis above with no task-specific coordinates or
   stored outputs. The next local run checks all five public demonstration pairs.

Remaining uncertainty is limited to masked-query scoring, which the solve tool
withholds for independent replay. The implementation is intentionally generic
for any rectangular grid in the demonstrated rule family.
