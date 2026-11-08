# Solve work log

## Exposure declaration before solving

I had not opened task `22e428cda452`'s generator, rule, notes, solutions, audit
records, or private labels.  I used only `solve-blind/challenge.json` and the
visible-only checker.

## Revision 1 — corner-local glyphs

**Observation.** Color 7 is the dominant background.  Every non-background
input cell is a corner cue.  The top-left and top-right examples replace their
cue with the same mirrored 2×2 block, inset one row and one column from the
nearest edges.  The two bottom-left occurrences replace their cue with the same
three-cell stroke at relative coordinates `(-3,+2), (-2,+2), (-1,+3)`.
Multiple cues compose without interacting.

**Hypothesis.** Clear the cue cells, then stamp the corner's learned template in
the cue color.  Mirror each template horizontally for a right-hand corner.  The
two test inputs use only the directly observed top-right and bottom-left cases;
the bottom-right mirror is included as the simplest symmetry completion but is
not needed for the visible queries.

**Alternatives considered.** A generic translation, diagonal ray, or size-based
shape does not fit both the 2×2 top glyph and the three-cell bottom glyph.  The
consistent repeated bottom-left output across different grid sizes supports
fixed offsets from the corner rather than proportional placement.

**Remaining uncertainty.** No visible example contains a bottom-right cue, so
that mirrored template is an extrapolation.  The queried corner types are both
observed directly.
