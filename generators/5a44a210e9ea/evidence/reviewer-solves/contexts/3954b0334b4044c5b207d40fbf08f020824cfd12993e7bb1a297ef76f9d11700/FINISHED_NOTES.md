# Visible-only solve work log

This is a human work log for the exposed post-repair episode. It is not a blind solve and not a token-level model trace.

## Attempt 1 hypothesis

Drop the first row after reading every nonzero entry in it from left to right as an ordered palette; zeros inside that row are separators, not a stopping signal. In the remaining body, split colour-1 cells into 4-connected components. Keep a component only when it equals the complete perimeter of its bounding rectangle, rank those valid frames by bounding-box area from largest to smallest, and recolour them by palette depth. Reuse the last palette colour when there are more frames than colours. Start from a blank output so malformed connected components disappear.

Visible evidence:

- Pair 1 has four nested frames but palette `[5, 4]`; all frames after the first use `4`.
- Pair 2 contains an outer frame plus a connected inner frame-like object with extra cells; only the outer frame survives.
- Pair 3 places four palette colours after zero gaps and all four are consumed.
- Pair 4 combines a gapped two-colour palette, three valid frames, and a malformed center; the third frame reuses the second colour and the center is erased.

No Racket source, generator source, private label, or previous solve explanation was consulted during this solve phase. Earlier rule exposure from the generator review will be declared at finish.
