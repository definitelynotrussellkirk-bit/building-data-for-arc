# Exposed, visible-only solve work log

This is a reviewer-authored work log, not a captured token-level conversation.
Earlier exposure: **yes**. I repaired this task's generator and read its rule
before this phase. During this solve phase I kept the generator, rule, reference
solutions, old solution explanations and private labels closed. I read only the
visible challenge, computed its visible changes in Python, and wrote this solver.
The earlier knowledge cannot be undone; this is not a blind reasoning benchmark.

## Observations and first genuine hypothesis

All three examples preserve shape and original nonzero cells. Visible green-cell
additions number 2, 1 and 2. The second example is a direct rectangle completion:
red at (5,6), (5,9), (10,6), new green at (10,9), with zero-based coordinates.
The first example has two separate red support groups. The third has interacting
support: red at (3,4), (5,3), (5,13), (6,3), (6,4). It adds (3,3) and (6,13),
while preserving the occupied color-9 corner at (5,4). It does not propagate to
(3,13) using a newly created green corner.

Hypothesis: complete empty fourth corners using only original red corners, in
one pass. Irrelevant colors are neither evidence nor writable background.

## Implementation choice and experiment

Use pairs of rows. A common red column supplies a complete vertical side;
columns red in exactly one row identify potential missing corners in the other.
Write only into original zeros, and compute every red-column set before any
writes. This naturally avoids cascading and preserves all occupied cells.

The visible-change probe is retained in visible-probe.json. I submitted this
single genuine solution with intent=solve. No deliberate wrong answer or failed
revision was manufactured. The check tool determines visible-example agreement
and execution only; query correctness remains withheld for maintainer scoring.

## Stopping reason

The solution is consistent with all visible transformations, including the
occupied corner and the non-cascading example. Stop after the first submitted
revision if its visible check passes. There is no claim that these finite
examples uniquely characterize every possible competing program.
