# Example-only solve record

This is an assistant-authored experiment summary, not a captured model conversation,
token-level reasoning trace, or log-probability record.

## Exposure and boundary

Earlier rule exposure: **yes**. Before this solve phase I read and modified the
assigned generator and read its canonical Racket program as part of the required
generator review. This is therefore **not a blind solve**. After `prepare`, I
consulted only `solve/challenge.json`, authored Python experiments, and visible-only
checker feedback. I did not open the generator, Racket/reference source, earlier
solution explanations, or private answers during this solve phase.

## Observations and hypothesis tests

The four visible demonstrations have four color-9-separated panels. Outputs have
the search panel's dimensions. Selector colors observed are 2 and 3. The generalized
demonstrations separate the selected template's color from the selector's color.
One demonstration includes overlapping template occurrences. All output marks are 8.

`probes.py` compares exact union-of-mask matching against five deliberate alternative
hypotheses using the four visible inputs/outputs only. The alternatives are
**intentional diagnostic negatives**, not claimed accidental failed model attempts.
`probe_results.json` retains their actual per-demonstration mismatch indices.

The submitted hypothesis crops the selected template, tests its nonzero colored
cells at every unrotated placement, ignores template zero cells, and unions all
matched footprints. Choosing panel 0 for selector 2 and panel 1 otherwise matches
the observed branches; behavior for other selector colors is an extrapolation not
established by these four examples alone (and is subject to the earlier exposure).

## Revision record

Revision 1: `solution.py`, standard-library-only Python, no generator imports.
It scans the original board without modifying it, so overlaps are retained.
The visible probes show 4/4 agreement; the five alternative hypotheses each fail
at least one visible demonstration. There were no subsequent solution revisions.

## Stopping condition and limitations

Stop after visible-only checker acceptance and successful query execution. The two
masked-query outputs remain unscored here. No claim of private-query correctness or
independent/blind inference is made. Generalization beyond the observed selector,
shape, and color combinations is not established by this small episode.
