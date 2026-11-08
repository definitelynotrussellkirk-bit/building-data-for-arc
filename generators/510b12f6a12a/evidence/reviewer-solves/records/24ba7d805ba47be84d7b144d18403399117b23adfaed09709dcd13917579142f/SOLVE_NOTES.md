# Solve work log

## Prior exposure

Before this blind episode I had not opened task `510b12f6a12a`'s generator,
reference rule, private labels, earlier solutions, or audit records. I had read
only the packet-level instructions and this episode's visible `challenge.json`.

## Revision 1 — crossing rays stopped by gray blockers

Hypothesis: each `2` on the top edge launches a vertical ray downward and each
`1` on the left edge launches a horizontal ray rightward.  A `5` blocks the ray
that reaches it, and cells reached by both still-active rays are painted `6` in
an otherwise-zero output.

Evidence from the visible pairs:

- In example 3, there are no blockers, and the output is exactly the Cartesian
  product of the two marked rows and four marked columns.
- In example 2, the two top rays meet blockers immediately in row 1, so neither
  reaches either marked row and the output is empty.
- In example 1, the top ray in column 1 is stopped at row 2 and the horizontal
  ray in row 3 is stopped at column 2.  Therefore only row 1 receives both top
  rays, matching the two output cells.

I first added a visible-example regression test and confirmed the untouched
stub failed with `NotImplementedError`.  I then implemented the ray simulation.
The principal alternative was “blockers merely delete their own cell,” but that
would incorrectly paint later crossings in examples 1 and 2.

Predicted masked outputs before running the checker:

- Query 1: `(1,6),(1,8),(2,6),(2,8),(4,6)` become `6`.
- Query 2: `(2,1),(2,5),(2,9),(4,1),(5,1),(5,5),(5,9),
  (7,1),(7,5),(7,9)` become `6`.
