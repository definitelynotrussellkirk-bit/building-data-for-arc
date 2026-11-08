# Solve work log

## Prior exposure

Before this blind episode I had not opened task `d833a288bd7d`'s generator, rule,
notes, solution, audit records, or private labels. I had only read the packet's
assignment instructions and the visible `solve-blind/challenge.json`.

## Revision 1 — rotate the square and advance its corner marker

The non-background object is a square made from colors 1 and 8. In every visible
example its output is exactly a 90-degree rotation in place. The four yellow
cells split into (a) one marker on a diagonal corner just outside the square and
(b) three points forming an axis-aligned L elsewhere.

I compared the L's horizontal arm across the examples. When its endpoint lies to
the **left** of the L corner, the square rotates clockwise; when it lies to the
**right**, the square rotates counterclockwise. The outside yellow marker advances
one square corner in that same direction, while the three-point cue disappears.
This reproduces all three visible outputs exactly:

- NW marker → NE plus clockwise rotation when the cue arm points left;
- NE marker → NW plus counterclockwise rotation when the cue arm points right;
- SW marker → NW plus clockwise rotation when the cue arm points left.

The implementation locates the 1/8 bounding square, identifies the exact outside
corner marker, derives the cue direction from the unique same-row arm, clears all
yellow cells, rotates the square, and writes one yellow marker at the next corner.

Remaining uncertainty: the visible examples establish the cue convention only
through these three layouts. Both test cues have right-pointing horizontal arms,
so I apply the observed counterclockwise rule. I did not inspect any reference
implementation or labels.
