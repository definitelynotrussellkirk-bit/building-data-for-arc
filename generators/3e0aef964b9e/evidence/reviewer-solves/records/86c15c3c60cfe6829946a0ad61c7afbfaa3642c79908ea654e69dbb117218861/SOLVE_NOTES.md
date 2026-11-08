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
