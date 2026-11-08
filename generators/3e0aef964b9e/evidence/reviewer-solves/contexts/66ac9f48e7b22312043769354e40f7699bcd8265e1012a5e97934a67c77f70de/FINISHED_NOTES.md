# Visible-only solve work log

## Access and exposure declaration

I am the delegated visible-only solver. For this post-repair solve I read only
this lane's `README.md`, `challenge.json`, and initial `solution.py` and
`SOLVE_NOTES.md` scaffold. I have not read generator or Racket source, canonical
data, task notes, reference solutions, private labels, outside checks, or earlier
explanations of this task. I previously analyzed the separate, visibly different
beam-and-mirrors blind challenge; that supplies no rule for this challenge.
The root reviewer has earlier source exposure in this review session. Therefore
the session-level finish declaration must be `--earlier-exposure yes`, despite
my own lack of source exposure. Reference consultation is `no`.

## Revision 1: count loose cells and fill a matching object's gaps

Observation: all examples preserve dimensions and color counts. A sparse color
moves from otherwise empty background into gaps of one larger-color object.
The number moved equals the number of gaps filled. Example 0 moves two 9s into
a square with two gaps, leaving squares with one and three gaps untouched.
Example 1 moves one 2 into the gap between the arms of the smaller diagonal V.
Example 2 moves three 4s into the upper-left 6 object, including its grid-corner
pocket; background outside the lower diagonal outline stays unchanged.

Hypothesis: identify background by frequency, loose paint as the rarer of the
other colors, and object groups by eight-neighbor connectivity. Gaps are
background between same-object cells in a row or column, plus pockets closed by
that object and grid edges. Fill the unique object with as many gaps as loose
paint cells, and clear the original loose cells. A four-neighbor background
flood within each object's bounding box identifies closed edge pockets.

Alternatives considered without program revisions: a bounding-box fill would
incorrectly fill exterior corners of the diagonal shapes. Pure enclosed-hole
filling would miss the square's open edge notch and gaps above the Vs. A convex
hull alone would miss example 2's isolated upper-left corner pocket. The union
of row/column gaps and closed pockets covers these visible distinctions.

Implementation written once, with no earlier candidate submitted. No hidden
query correctness is known or claimed. Remaining uncertainty includes equal
foreground frequencies, nonunique matching objects, and unseen shapes whose
intended interior differs from this row/column-plus-pocket hypothesis.

First frozen check command, run from the outer `arc_review` directory:

```sh
WORK/.venv/bin/python3 review.py solve check --intent solve --note 'Revision 1: move sparse paint into the unique same-count object gaps; row/column gaps and grid-edge pockets explain all visible shape distinctions'
```

Result: pending execution below; the checker reports visible correctness and
execution only. The code and this hypothesis are frozen by the command.

### Observed revision-1 result

The first check exited 0: `execution_status=completed`, `visible_passed=3`,
`visible_total=3`, `revision=1`, `reported_label=unknown`, and
`training_admitted=false`. Program hash:
`2f55a9f1c50a719a4e7a4db998209574f877bf097ad6b26b79dc4504935e41f2`.
No solution changes followed this result.

Additional own-Python probe command: `WORK/.venv/bin/python3 - <<'PY' ... PY`
from the same outer directory. The inline script imported only this lane's
solution and challenge, applied each of four rotations to both the original and
horizontally reflected visible input/output pairs, and asserted matching solves.
It also asserted that each original input remained unchanged. Observed result:
`Visible-derived reflection/rotation probes passed: 24/24; original inputs unchanged`.
These are transformations of visible examples, not independent hidden evidence.

Finish command:

```sh
WORK/.venv/bin/python3 review.py solve finish --earlier-exposure yes --reference-consulted no --reason 'One actual solution revision passes all 3 visible examples and 24 visible-derived symmetry probes; no hidden labels were accessed; session root had source exposure while this delegated solver did not'
```

Stopping rationale: the single implemented hypothesis fits every visible example
and the shape/orientation probes. Hidden labels remain unknown. The declared
session source exposure is yes because of root's earlier access, while reference
consultation is no. There are no fabricated failed attempts or unseen-correctness
claims in this log.
