# Solve work log

## Prior exposure

I had already inspected and repaired this task's generator before this solve, so
my earlier rule exposure is **yes**. During this solve I did not reopen the
generator, the Racket rule, reference solutions, private labels, or earlier
solution explanations. I used only the visible presentation produced by
`solve_episode.py prepare` and my own Python implementation.

## Revision 1 — panel thickness equivalence

Observed:

- Every full-height column of color 9 separates adjacent objects into panels.
- The output side length equals the number of panels.
- Every output diagonal is 8, so the output is a pairwise relation matrix.
- Off-diagonal 8s group objects that have the same apparent *interior
  thickness*, even when their color, area, silhouette, and bounding box differ.
  For example, train 0 groups panels 0 and 2 while separating panel 1; train 1
  groups panels 1, 2, and 3 while grouping 0 with 4.

Hypothesis: repeatedly remove every cardinal boundary cell from each panel
object. The number of removal rounds is its thickness. Emit 8 for a pair of
panels exactly when their removal-round counts agree, otherwise 0.

Probe: I first added `solve/test_visible_examples.py`; with the untouched
solution stub it failed with `NotImplementedError`, confirming the test exercised
the missing behavior. I then implemented full-height-divider splitting,
cardinal onion peeling, and the equality matrix.

Alternatives considered: raw area, color, bounding-box dimensions, and rectangle
width. The visible examples vary these properties within the same output class,
so none is a stable explanation. A bbox-only approximation is especially risky
for the nonrectangular thin-but-wide objects.

Remaining uncertainty: the visible examples do not define behavior for malformed
or empty panels. The submitted solver raises on an empty panel and otherwise
implements the simplest rule consistent with all visible demonstrations.
