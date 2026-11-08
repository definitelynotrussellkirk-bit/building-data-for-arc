# Blind solve work log

## Scope and exposure

Assignment: review-cc6df0b7bf591ff4. Task: db4cb6bcf6fe.
I had no earlier exposure to the task rule. During this solve I opened only the
public blind README, challenge.json, the initial solver/work-log templates,
my own Python files, and public command feedback. I did not consult generator
source, the Racket rule, reference solutions, canonical data, private query
labels, or prior solution notes. This is a concise human-readable work record,
not a raw internal token trace.

## Preparation

All commands run from /tmp/arc_review_121953_mount inside the approved namespace
with TMPDIR=/tmp/arc_review_121953_mount/tmp.

- `python3 review.py setup`: exit 0; Racket runtime ready.
- `python3 review.py blind prepare`: exit 0; preparation stdout retained in
  WORK/checks/blind-prepare.log. Three visible training pairs and two masked
  queries were provided.

## Observations and candidate rule

Each input has four nonzero colors, four points per color, and each visible
output is a symmetric 4 by 4 matrix. Its diagonal is always 5; off-diagonal
entries are either 0 or 8. This suggests a relation among the four patterns.

The candidate is equality of normalized convex hulls: remove translation and
disregard points lying on edges or within the outer triangle. Use ascending
color order for the matrix. Place 8 where two distinct colors have equal hulls,
5 on the diagonal, and 0 elsewhere.

Concrete evidence from the displayed examples:

- Training 0: colors 3 and 8 share the same right-ended downward triangle;
  their intermediate top point differs. Colors 5 and 6 share the same
  downward triangle with the lower vertex centered; one extra point is
  internal and the other is on the top edge.
- Training 1: colors 3 and 8 share an upward triangle. Colors 5 and 7 are
  mirror-oriented triangles, so they do not match. This rules out allowing
  arbitrary reflection as part of equivalence.
- Training 2: colors 3, 6, and 7 share one triangle, while color 2 has the
  opposite orientation. Ascending colors [2, 3, 6, 7] explain the isolated
  first row/column and the three mutually matching final entries. Spatial
  reading order would incorrectly isolate the third pattern.

Exact equality of all occupied pixels would miss the visible matches.
Reflection-invariant equivalence would add incorrect matches. These were
rejected by inspecting the public examples, not by submitted solver failures.
No deliberately failing attempt was fabricated.

## Revision 1

Implemented solution.py with a monotone-chain convex hull, removing collinear
edge points, normalized by each color bounding box origin. Colors are sorted
numerically. A small standalone public-data diagnostic, probe_hulls.py, prints
the inferred hulls and predictions and compares only available training
outputs. Query predictions are printed without asserting correctness.

The first file-writing shell invocation failed with exit 2 due to quoting,
before any solver code was written. It was corrected by quoting the shell
script as one argument. This was a command construction error, not a solver
check failure.

Planned probe: `python3 WORK/solve-blind/probe_hulls.py`, with output retained in
WORK/checks/blind-hull-probe.log. The official check follows this genuine first
implementation and freezes this code and log.

## Remaining uncertainty

Only the visible examples are available. Equality of convex hulls is the most
compact rule I found explaining all of them. Query correctness remains unknown
until the independent evaluator checks the masked labels.

## Public probe result

`python3 WORK/solve-blind/probe_hulls.py` exited 0. All three visible training
predictions matched exactly. Both masked queries produced 4 by 4 predictions;
no expected query outputs were accessed. No code revision was needed after
the probe. Full hull signatures and predictions are retained in
WORK/checks/blind-hull-probe.log.

Official check request for revision 1:
`python3 review.py blind check --intent solve --note 'Revision 1: compare normalized convex hulls in ascending color order; the public probe matches all three visible training pairs.'`

## Official checker infrastructure interruption

The first official check invocation terminated with exit 137 (process killed)
before an attempt receipt was created. The public summary still reported
status prepared and attempt_count 0. This is not counted as a visible-example
failure. The initial log WORK/checks/blind-check-1.log is empty because the
checker emitted no output. The public summary and available disk/memory were
then inspected; the summary exposes generation metadata but no hidden labels
or source code. The solver itself was already written and the public probe
had already passed before that inspection. An unchanged-code retry follows.
