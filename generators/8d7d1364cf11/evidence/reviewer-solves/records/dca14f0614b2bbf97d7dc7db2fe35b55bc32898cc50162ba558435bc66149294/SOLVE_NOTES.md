# Exposed post-repair solve notes

This is a human work log based only on the prepared visible challenge. I had
already inspected the assigned generator and authority during the repair phase,
so earlier rule exposure is **yes**; I did not consult either after preparation.

Across the three demonstrations, background is 4. Non-background 8-connected
components split into multicolor source shapes (size > 1) and isolated dots.
Each productive dot has a color that occurs in one source shape. The output is a
fresh all-4 canvas containing a translated copy of that whole source, with the
same-colored source cell aligned to the dot. Dots whose colors are absent from
all sources disappear. Original sources and dots are not retained.

Revision 1 implements exactly that visible rule with an independent component
finder. The examples show no need for a competing top-left anchor, source
preservation, or decoy stamping, so I am checking this directly rather than
inventing a failed revision.
