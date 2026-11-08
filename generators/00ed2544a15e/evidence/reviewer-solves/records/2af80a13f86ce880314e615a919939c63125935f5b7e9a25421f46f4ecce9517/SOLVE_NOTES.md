# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
labels, prior solve explanations, or any catalog record before solving. I used
only the visible examples printed by `solve_episode.py blind prepare` and the
matching `solve-blind` files.

## Revision 1 — unobstructed red-to-red orthogonal segments

**Hypothesis.** Color 2 cells are endpoints. For every pair of 2 cells in the
same row or column, replace every intervening background cell (0) with color 8
when the entire open segment is background. Any nonzero cell between the two
endpoints blocks the whole segment. Other colors are obstacles and otherwise
remain unchanged.

**Evidence from the visible examples.**

- Example 0 connects the 2 at `(3,4)` to aligned 2s at `(0,4)`, `(3,1)`, and
  `(3,7)`. The aligned pair `(3,7)`–`(7,7)` is not connected because a 9 lies
  on that column at `(5,7)`.
- Example 1 fills the clear vertical chain through column 5 and the clear
  horizontal segment on row 3; the unaligned 2s remain isolated.
- Example 2 does not draw toward the aligned 2 at `(3,7)`, because color 3 at
  `(3,6)` blocks that segment. This rules out merely drawing rays from a
  central 2 and supports an all-or-nothing clear-segment test.

**Probe.** I first ran a visible-example harness against the untouched skeleton;
it failed with `NotImplementedError`, confirming the test exercised `solve`.
I then implemented pairwise row/column checks against an immutable copy of the
input, so newly painted 8s cannot create or suppress later connections.

**Alternatives considered.** A "choose one central 2 and draw three rays" rule
fits much of the data but is less general and does not naturally explain all
aligned pairs. A rule that paints until the first obstacle would incorrectly
paint `(3,5)` in example 2, so the implementation requires the complete segment
to be clear before painting any of it.

**Remaining uncertainty.** The examples consistently use 2 as the endpoint
color and 8 as the connector. They do not show adjacent endpoints (the empty
segment is treated as valid) or crossing segments away from an endpoint; the
pairwise rule gives deterministic behavior for both.
