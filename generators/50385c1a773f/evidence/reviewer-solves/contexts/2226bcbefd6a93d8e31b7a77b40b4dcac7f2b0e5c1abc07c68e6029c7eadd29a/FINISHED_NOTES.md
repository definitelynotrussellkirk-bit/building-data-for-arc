# Blind solve notes — 50385c1a773f

This is a human visible-example work log. I did not inspect the generator, Racket rule, private labels, prior solutions, or audit records.

## Observations

- Color 2 is the start. Present waypoint colors appear ordered as 2, then 4 when present, then 3 when present.
- Zeros strictly between consecutive colored waypoints become 8; the colored cells remain unchanged.
- After the last colored waypoint, the path makes a 90-degree turn relative to the incoming segment.
- Gray cells choose the side of that final turn. If gray lies directly on the ray, the ray stops at the gray cell; otherwise it reaches the grid boundary.
- Other gray components can be distractors. An aligned gray component is stronger evidence than an unaligned one.

## First implementation

Implemented the ordered axis-aligned joins and a final perpendicular ray. For the ray, prefer the nearest aligned gray cell; otherwise choose the side using the nearest gray clue in the relevant coordinate and continue to the boundary. This predicts the first test as a 2→4→3 path ending against the gray run on the lower row, and the second test as the same path ending against the left gray run; the gray run to the right of 4 is ignored because 4 is an intermediate waypoint.
