# Post-repair visible-only solve

## Exposure and evidence boundary

This is an exposed solve: I previously reviewed the generator and its rule as
part of the repair. After `review.py solve prepare`, I used only its visible
presentation, `solve/challenge.json`, and Python. I did not reopen the generator,
Racket source, canonical helpers, prior solution explanations, or private query
labels during this episode. These are concise authored work notes, not a
captured token-level model conversation or an unbiased induction experiment.

The public challenge contains three labeled demonstrations and two masked
queries. The preparation record binds it to final generator SHA-256
`23e1cd94475e1a4b8ad285a8cfefbae488c04cbb1d5c4e8009472345548b83f2`.

## Visible observations and hypothesis

Example 2 gives the simplest pattern: connect the matching 3 endpoints and the
matching 8 endpoints along their opposite 45-degree diagonals. Only the gaps
are added; endpoint colors and background elsewhere are preserved.

Example 0 shows guards. Color 6 has two endpoints but is not diagonal and stays
unchanged. Color 7 is diagonal but its interior contains an 8 at `(3,7)`, so it
does not extend. Color 8 occurs three times and stays unchanged even though two
occurrences have an empty diagonal between them. The eligible 1 and 4 diagonals
cross at `(8,3)`, where the visible output is 4. Color 1 appears first at `(7,2)`
and color 4 later at `(7,4)`, supporting later input reading order at the cross.

Example 1 refutes the opposite numeric explanation: color 6 appears at `(4,0)`
and color 5 later at `(5,5)`, and 5 wins their crossing at `(7,3)`. Color 1 is
blocked by a 7, while three-occurrence 7 remains unchanged. The two crossing
examples together support input reading order rather than either numeric order.
Both crossing paths complete, so eligibility must use the original input rather
than the progressively painted result.

Proposed rule: enumerate nonzero colors in first row-major occurrence order.
For colors occurring exactly twice, require a diagonal span of at least two
and an all-zero interior in the input. Paint those interior cells in that
color into a copy, letting the later eligible color overwrite crossing gaps.

## Probes and implementation revision 1

`visible_probes.json` compares this rule and five deliberately wrong hypotheses
only against the three visible outputs. The proposed solution matches all three;
ascending/descending numeric order, ignoring blockers, ignoring exact-two
cardinality, and testing painted-output eligibility each fail at least one.
Those rival probes are intentional diagnostics, not failed solver revisions.

Revision 1 implements the proposed rule in plain Python. A dictionary populated
in reading order preserves color order, a separate copied result prevents
painting from changing eligibility, and all masks are computed from the supplied
input. I will use the standard visible-only check and preserve its actual result.
