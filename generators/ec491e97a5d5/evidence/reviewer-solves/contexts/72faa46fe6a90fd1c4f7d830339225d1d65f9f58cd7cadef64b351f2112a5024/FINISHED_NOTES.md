# Solve work log

This is an authored work log of observations, implementation choices, and
validation results. It is not a verbatim reasoning trace.

## Evidence boundary

Before implementation I read only this folder's README.md, challenge.json,
initial solution.py, and initial SOLVE_NOTES.md. I have no earlier exposure to
the Racket rule and have not consulted generator code, reference solutions,
private query labels, or earlier solution explanations.

## Revision 1

The three visible training examples preserve the grid shape and every colored
rectangle's boundary, while replacing its strict interior with zero. Rectangles
of height two have no interior and remain unchanged. Touching rectangles of
different colors are treated separately; separated rectangles of the same color
also remain separate objects.

Implemented this hypothesis by finding four-connected monochromatic components,
checking that each fills its bounding rectangle, and clearing the strict interior
of those rectangles. The original grid supplies the connectivity; the result is
a copy. This avoids allowing an earlier edit to alter a later object's detection.

No alternative program or failed revision has been tested. A per-color bounding
box would incorrectly join the separated same-color rectangles seen in the
examples, so it was not implemented. Behavior for nonrectangular components is
not established by the visible examples; this program leaves them unchanged.

Validation command run from the packet root:

    python3 review.py blind check --intent solve --note 'Revision 1: hollow each solid monochromatic connected rectangle; visible examples require independent treatment of touching colors and separated same-color objects.'

Observed result: revision 1 completed successfully and matched 3 of 3 visible
training outputs. The feedback reported label "unknown". No code revision was
needed after that check, and there have been no failed attempts to remove.

Query outputs are unknown. Execution feedback on them cannot establish query
correctness.

## Stopping decision

The single implementation matches every visible example, and the query inputs
contain the same kinds of colored rectangles. I am stopping after the successful
visible check without claiming private query correctness. The intended final
declaration is earlier exposure "no" and reference consulted "no".
