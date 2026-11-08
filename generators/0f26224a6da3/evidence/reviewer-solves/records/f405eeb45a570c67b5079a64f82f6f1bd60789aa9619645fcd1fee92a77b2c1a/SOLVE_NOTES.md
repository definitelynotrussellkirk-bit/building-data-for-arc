# Fresh visible-example solve

## Provenance and restrictions
This is an author-written experimental work log, not a captured model conversation or token-level trace. I previously read and modified this task's generator and read its Racket authority during generator review. Therefore this is **not a blind solve**. After preparing this episode, I opened only the visible challenge and my newly written solve/probe files; I did not consult the generator, Racket source, prior solution explanations, or private query labels during the solve.

## Visible evidence and selected hypothesis
The three demonstrations preserve each source color and extend isolated cells by one cardinal step. Cardinally touching cells remain unchanged, including a mixed-color adjacent pair. A diagonal same-color pair still expands, so isolation is four-neighbor rather than eight-neighbor. Boundary extensions are clipped rather than rejecting boundary sources.

## Recorded experiments
`probe_visible.py` compares three deliberately selected rival hypotheses against the visible demonstrations: expanding every foreground cell, ignoring boundary sources, and requiring eight-neighbor isolation. These are diagnostic comparisons, not genuine failed solve attempts. Their per-demonstration outcomes are retained in `visible_probe.json`.

The first submitted candidate is `solution.py`. It tests isolation against the original input, writes into a copy, and preserves the original foreground. It matches all three visible demonstrations. Both query inputs execute without mutation and retain their dimensions. Query correctness is not available to me.

## Ambiguity and stopping condition
The visible overlapping expansions use the same color. They do not identify a policy for conflicting expansions of different colors. The implementation uses first-writer preservation for that unobserved case; no generalization claim is made about it. No genuine failed candidate was produced, and no failure was manufactured. Stop after the visible checker confirms execution and the three demonstrated transformations; leave masked-query scoring to the maintainer.
