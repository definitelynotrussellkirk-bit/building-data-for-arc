# Fresh visible-example solve

This is an assistant-authored engineering work log, not a captured token-level
model conversation. No token probabilities or hidden model traces were recorded.
Earlier rule exposure: **yes**, from the preceding generator repair and audits.
This is **not a blind solve**. During this phase I read the visible
`challenge.json` and used the Python files created here; I did not reopen the
generator, Racket rule, previous solution explanations, reference programs or
private labels. The preparation tool's automatic Racket execution is not a
manual reference consultation.

## Revision 1 — local frame completion

Observed in the four visible pairs: the 9-valued rectangular walls and exterior
stay fixed. Inside each frame, the top marker specifies a column and the left
marker specifies a row. Both interior lines are completed in their shared color.
Visible examples 2 and 3 (one-based) each contain two frames sharing a color,
which rules out completing just one frame per color. The row and column stop at
the frame's interior boundary, rather than continuing across the canvas.

Implemented `solution.py` using 4-neighbor wall components, independent frame
bounds, and local marker positions. Color labels are not used as object IDs.
The function copies its input and imports no repository code.

Probes in `experiments.py`: exact agreement on all four visible pairs; input
immutability; seven marker-color permutations per pair; zero-padding translation
per pair; and successful masked-query execution with walls preserved. None of
these probes reads a masked expected output. There were no failed implementation
revisions, and no deliberately wrong solver was submitted.

The official checker is run once on this revision. Its feedback establishes only
visible-example correctness and execution, not masked-query correctness. Stop
when the visible examples, metamorphic probes, and checker agree; leave the two
masked answers for independent maintainer scoring. No broader claim of unique
rule inference or improved learner accuracy is made.
