# Solve work log

## Prior exposure

I had already inspected this task's generator and authority during the repair,
so this is an **exposed post-repair solve**, not a blind solve.  After
`solve_episode.py prepare` I did not reopen the generator, Racket source,
reference solutions, or private query labels; I used only the visible examples
printed by preparation and the visible-only checker.

## Revision 1 hypothesis

The background is cyan 8.  Each other color forms one 8-connected object aimed
toward the grid center.  The unique largest object is special.

For every object, identify its cell nearest the geometric grid center (the
inward-pointing tip).  The output removes that tip from each of the three
smaller objects but retains the largest object's tip.  It also paints a
three-cell bar of the largest object's color immediately outside that object's
opposite/outward bounding-box edge, centered on the tip's row or column.

I implemented the rule independently using 8-connected component extraction,
cell counts, squared distance to the grid center, and the tip's displacement
from its own bounding-box center to choose the outward edge.  A possible
alternative was to infer the sector only from the component centroid or canvas
quadrant; the visible examples make the unique nearest cell the more direct and
rotation-consistent anchor.

Remaining uncertainty before checking: a pathological object could tie for the
nearest cell or largest size, but every visible lesson has unique choices.
