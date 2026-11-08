# Fresh visible-example solve — review-248201d73dc2f3a9

This is a reviewer-authored experiment/work summary, not a captured model
conversation, token-level reasoning trace, or blind evaluation. Earlier exposure
to this task's rule occurred during the generator repair. After preparation I
opened only `challenge.json` as puzzle evidence. I did not consult the generator,
Racket source, previous solution explanations, reference solutions, or private
labels during this phase.

## Attempt 1 — object-vertex relocation and enlargement

The three visible examples retain their dimensions and dominant background.
Small connected L-shaped objects become larger border Ls. An object's occupied
right-angle vertex determines its output corner; its current location does not.
The visible single-object example supports leaving the other corners empty.
The third visible example contains repeated colors in separate components, so
colors alone cannot identify the objects. A side of eleven uses arms of five
cells; a side of nine uses arms of four.

Implementation: infer the dominant color; extract four-connected components
separately for each other color; require a three-cell 2×2 L; locate the vertex by
its two orthogonal neighbors; draw that color at the corresponding border corner
with arm length `height // 2`. Components of color zero are processed normally.
The solver uses only the Python standard library and does not mutate its input.

Probe: `python3 solve/visible_probe.py` compares only the three visible pairs and
checks input non-mutation. Then the official episode checker records the first
actual solution revision. No deliberately wrong solution or fabricated failed
attempt was introduced. Masked-query correctness is not inferred from successful
execution or visible-example agreement.

Observed result: the visible probe passed 3/3; the official first revision also
passed 3/3 visible examples and completed execution. Its reported query label is
`unknown`, as required. I stopped after the first supported revision rather than
using the masked queries as a tuning signal. Final query scoring is deferred to
independent maintainer intake. Earlier rule exposure: **yes**. Reference
consulted during this solve phase: **no**.
