# Solve work log

I began with no earlier exposure to task `f6b9f647b109`'s generator, Racket rule,
private labels, or solution explanation. I used only the visible examples emitted
by `python3 review.py blind prepare` and the files in `WORK/solve-blind/`.

## Revision 1 — red-oriented shortest route

At first I considered a generic Bresenham-like straight line or any shortest
8-connected path between the blue `1` and red `2`. The exact placements rule out
both underspecified alternatives: the same ordering appears in every example when
the route is read **from red toward blue**.

The observed construction is:

1. Move one cell diagonally from red toward blue when both coordinates differ.
2. Use all currently unmatched motion along the major axis (vertical or horizontal).
3. Finish with diagonal steps until reaching blue.
4. Color only intermediate cells green (`3`), preserving both endpoints.

Checks against the examples:

- Example 0: red `(2,15)` first reaches `(3,14)`, runs vertically to `(9,14)`,
  then diagonals to blue `(13,10)`.
- Example 1: red `(5,8)` first reaches `(4,7)`, runs horizontally to `(4,4)`,
  then diagonals to blue `(1,1)`.
- Examples 2 and 3 give the same one-diagonal / major-axis / diagonal ordering.

Predicted queries:

- Query 0: green at `(8,1)` and `(9,1)`.
- Query 1: green at `(9,2)`, `(8,2)`, `(7,2)`, `(6,2)`, and `(5,1)`.

The implementation also handles same-row/same-column and very close endpoints by
omitting phases that have zero length. Remaining uncertainty is only whether
unseen instances deliberately exclude such degenerate placements; the visible
rule itself remains well-defined for them.
