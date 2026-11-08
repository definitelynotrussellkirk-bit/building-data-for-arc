# Solve work log

## Prior exposure

Before this solve episode I had already reviewed this task's canonical examples,
selected Racket rule, and repaired generator. This is therefore an exposed
post-repair solve, not a blind solve. During the solve episode itself I consulted
only the visible presentation produced by `solve_episode.py prepare` and my own
solution code; I did not reopen the rule, generator, reference solutions, or
private labels.

## Revision 1 — connected rooms separated by color 1

All three visible demonstrations preserve every color-1 cell and replace every
zero in a 4-connected non-1 region with the region's single nonzero seed color.
The second demonstration is the decisive probe: the two rooms have dogleg
boundaries and are not rectangles, so the operation must be connectivity-based,
not bounding-box fill. The third demonstration confirms that a full divider can
create three rooms, each independently flooded.

Implemented a breadth-first search over all cells whose original value is not 1.
For each connected component, collect distinct nonzero colors. When exactly one
is present, replace only original zeros in that component with that color. This
also preserves walls and seeds, does not depend on border shape, and handles both
visible queries' irregular partitions.

Alternative rejected: identify rectangular chambers from runs of wall cells.
That fits visible examples 0 and 2 but fails the dogleg geometry in example 1.
