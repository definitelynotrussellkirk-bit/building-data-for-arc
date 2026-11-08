# Post-repair solve work log: 23a0c42b8a1c

## Exposure and source binding

This is the exposed post-repair solve. The overall repair session included earlier
source/rule-domain exposure, so the finish declaration will say
`earlier_rule_exposure=yes`. During this solve phase I used the public preparation
output, `README.md`, `challenge.json`, my own Python experiments on the visible
pairs, and public check feedback. I did not consult the generator, Racket source,
canonical helpers, reference explanations, or private query labels during this phase.

The public prepare command reports generator SHA-256
`4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b`,
matching the frozen source identity provided for this solve. The public challenge
SHA-256 is `a9ceae96a080979dbbee9ec9f3a4bdfa2af9f28727992ef33f0bad7b51f12f0e`.
It contains four labeled demonstrations and two test inputs without output keys.
The public instance hash is
`4baf7636bd276238d7d9d5a7528e73ab7fd5c44e11177c10c862930c938a357c`.

## Visible observations and hypothesis

Each input has a single color-1 marker. Other nonzero colors form compact shapes;
some tiny differently colored pieces touch a larger shape without belonging to
that shape's color. Every output consists of a cropped silhouette in color 8,
with zero cells preserving holes or missing corners.

My hypothesis is to find monochromatic components using orthogonal connectivity,
retain those sharing an edge with the color-1 marker, select the one with the
fewest occupied cells, crop its bounding box, and recolor its cells to 8.

The visible evidence is:

| Demonstration | Components touching 1 (color: cell count) | Selected shape |
| --- | --- | --- |
| 0 | 7:5; 8:6 | Color 7, a 3 × 2 mask with its upper-left cell missing |
| 1 | 6:8; 9:6 | Color 9, a 3 × 3 mask |
| 2 | 6:6 | Color 6, a 3 × 3 mask; the smaller distant color-4 piece is ignored |
| 3 | 2:5; 4:6 | Color 2, a 2 × 3 mask with its upper-right cell missing |

This makes pixel count relevant: competing touching shapes can have equal
bounding-box area while their occupied-cell counts differ. Splitting by color
also matters for the differently colored corner pieces in demonstrations 0 and 3.

## Visible experiment before solver revision 1

I ran `checks/post-repair-solve/analyze_visible.py` against only the four labeled
public training pairs. The experiment enumerated monochromatic components and
compared six explicit selection hypotheses after cropping and recoloring.

| Hypothesis | Exact visible matches |
| --- | ---: |
| Smallest touching component by occupied-cell count | 4/4 |
| Largest touching component | 1/4 |
| Smallest component anywhere | 0/4 |
| First touching component in reading order | 3/4 |
| Touching component with lowest color number | 3/4 |
| Smallest touching bounding box, then reading order | 3/4 |

Those alternatives were compared in the experiment; they were not submitted as
solver revisions. The actual results and exact command receipt are in
`checks/post-repair-solve/visible_hypotheses.json` and
`checks/post-repair-solve/visible_hypotheses.command.json`.

## Solver revision 1

Implemented the supported smallest-touching-component hypothesis in `solve(grid)`.
The program uses orthogonal flood fill for each nonzero color other than the
marker, tests edge adjacency to color 1, minimizes occupied-cell count, and emits
the selected mask in color 8. It reads only its input argument and keeps the
input unchanged.

Equal-size touching components are not demonstrated. The implementation uses
reading order as a deterministic fallback for ties; this is an extrapolation,
not an observed tie rule. These examples also do not distinguish every possible
connectivity convention. The intended domain outside the visible examples remains
unverified. Query predictions may be executed by the public checker, but private
query correctness is withheld.

The next command checks revision 1 with `--intent solve`, retaining its exact code
and this work-log snapshot. Its result will be recorded below after execution.

## Revision 1 results and stopping decision

The official public `review.py solve check --intent solve` completed with exit 0.
Its revision-1 receipt reports **4/4 visible examples passed**, execution status
`completed`, and correctness label `unknown`. The checked program SHA-256 is
`d70324567862822c806c15e1512e42ad46fc2e7f08e05a13b15be9cdcb4e7c7c`;
the work-log snapshot checked at that point has SHA-256
`f011a5b6294f8c13bcb0f6b178dfe7d50e936a8b9aca6ac2f6e43368e1cd9ce0`.
The official check again binds to the frozen generator hash stated above.
`checks/post-repair-solve/check_r1.command.json` and its complete stdout/stderr
retain the command, actual working directory, and feedback.

I then executed the unchanged solver on the two public query inputs using my own
Python, without labels. Both executions completed and produced valid 3 × 3
integer grids; both inputs remained unchanged. These are execution checks, not
query-correctness checks. The predictions and explicit withheld-correctness
status are retained in `checks/post-repair-solve/public_query_execution.json`,
with exact command/log receipts beside it.

One solver revision was authored and submitted. Its visible results support the
hypothesis, and there is no observed failure requiring a code change. I am
stopping after this successful visible check and the two query executions.
Unseen-domain behavior, equal-size tie semantics, alternative connectivity
conventions, and private query correctness remain unverified. The finish command
will record earlier exposure `yes` and reference consultation during this solve
`no`, and freeze the final work log.
