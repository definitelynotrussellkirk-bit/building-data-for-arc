# Blind solve notes — 6d33e42a400d

I used only `solve-blind/challenge.json`.

## Observations

- Every input has one dominant background and two foreground colours.
- The rarer foreground colour is a straight, evenly spaced guide: either one
  row of dots or one column of dots.
- The other foreground colour has a second guide at the same transverse
  coordinates plus an irregular drawing attached to the rare-colour guide.
- The output keeps the input and adds a rare-colour copy of that irregular
  drawing on the far side of the other-colour guide.
- The copy is reflected along the guide-normal axis.  Example: a source cell
  one row below the rare guide becomes one row above the receiver guide; a
  source cell three columns left of the rare guide becomes three columns right
  of the receiver guide.

## Hypothesis

Detect the rare guide, find the parallel receiver guide by matching all guide
coordinates in the other foreground colour, select drawing-colour cells on the
side of the rare guide opposite the receiver, and reflect them across the two
guides while recolouring the copy with the rare colour.  Preserve any existing
non-background cells.

## Implementation

`solution.py` implements the same logic for horizontal and vertical guides.  It
uses the closest complete matching receiver guide if more than one candidate is
present, and writes only into background cells.


## Revision after visible check

The first implementation passed 1/3 examples.  The failure was not the reflection
rule: I had selected the *closest* line containing all guide-aligned drawing
cells.  A dense row/column inside the source drawing can satisfy that condition
and be closer than the actual receiver guide.  I revised receiver selection to
prefer the candidate with the fewest drawing-colour cells (the sparse guide),
using distance only as a tie-breaker.
