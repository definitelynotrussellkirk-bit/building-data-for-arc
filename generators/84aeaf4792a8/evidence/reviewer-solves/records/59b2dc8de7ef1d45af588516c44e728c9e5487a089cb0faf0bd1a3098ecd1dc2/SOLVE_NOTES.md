# Visible-only blind solve work log

This is a concise assistant-authored work log, not a captured token-level model trace.
No generator, reference rule, canonical solution, audit record, or private label was opened.
Earlier exposure to this task's rule: none in this session; no known earlier exposure.

## Hypothesis before first check

There is one output row/column per foreground object, ordered by its first pixel
in row-major scanning. The diagonal is 5. Off-diagonal entries are 8 precisely
when two objects have the same shape up to translation and quarter-turn rotation;
other entries are 0. Object colors do not identify matrix rows.

Visible example 0 has four objects. The first (gray) and third (red) are
rotations of each other. The second (yellow) is a reflected version, and its
matrix links are absent: this distinguishes rotation-only equivalence from
equivalence under reflection. Example 1 links the four equal-arm L shapes and
leaves the T shape unmatched. Example 2 has two separate matching pairs.

Implementation: same-color four-connected components found by row-major scanning,
with a canonical key that takes the minimum normalized coordinate tuple over
four rotations. Query outputs are predicted by this same rule; no masked label
is requested or inspected. The visible layouts do not fully distinguish every
possible connectivity or ordering convention; this is the best supported rule.

Only genuine solve revisions will be retained. No failure was manufactured.
