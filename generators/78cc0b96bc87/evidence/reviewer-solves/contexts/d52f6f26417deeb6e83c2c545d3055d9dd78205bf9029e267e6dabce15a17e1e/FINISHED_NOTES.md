# Solve work log

## Exposure declaration

This is the required post-repair visible-only solve, not a blind solve. Before
preparation I had read the assigned generator, canonical record, and authority
while doing the repair, so earlier rule exposure is **yes**. After `solve
prepare` I did not reopen those sources, reference solutions, private labels,
or earlier solution explanations. The reasoning and implementation below use
the visible examples in this episode.

## Visible observations and hypothesis

Every input has one monochrome hollow rectangular frame on a zero background
and two differently colored cells in its strict interior. The two cells share a
row. Across all three outputs:

- the frame and the zero background outside it are preserved;
- the strict interior becomes a checkerboard using the two seed colors;
- the left seed's color occupies the frame interior's top-left cell;
- the right seed's color occupies the opposite parity.

Example 0 shows the seeds already at the interior top-left; example 1 moves the
adjacent pair away from that corner; example 2 separates them. Together these
rule out using literal seed position as the output phase and support using
left/right color roles. The output dimensions remain unchanged.

## Probe 0 — harness red check

I first ran the supplied `NotImplementedError` template as a deliberate
diagnostic probe. Expected result: execution error, confirming that the visible
checker exercises `solve(grid)` before I add the inferred transformation.

## Revision 1 — frame-local left/right checkerboard

Implemented the visible rule directly. The program detects the unique color
whose cells are exactly a rectangular perimeter, collects the two nonzero
strict-interior seeds, orders them left-to-right, and fills the strict interior
by parity from its top-left corner. It copies the original grid first, so the
frame and all outside cells stay unchanged. Invalid/underdetermined inputs are
returned unchanged rather than guessed; that fallback is not exercised by the
visible episode.

## Stopping decision

Revision 1 passes all three visible examples. Both queries have the same single
frame/two-seed structure, and the demonstrations explicitly cover corner,
shifted-adjacent, and separated seed placements, so no further rule change is
supported. Remaining uncertainty concerns malformed scenes outside the visible
grammar, not these two queries.
