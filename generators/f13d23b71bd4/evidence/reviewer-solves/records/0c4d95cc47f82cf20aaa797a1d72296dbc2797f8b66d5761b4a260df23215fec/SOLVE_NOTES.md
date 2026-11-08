# Solve work log

## Exposure before solving

I had not opened this task's generator, canonical rule, private labels, reference
solutions, notes, or audit evidence. I had read only the packet-level workflow and
general ARC design document before preparation.

## Revision 1 — move sufficiently large same-color components to the bottom

Visible-example observations:

- The background is the dominant color (7 in every shown example).
- Four-or-more-cell connected objects move straight down until their original
  bounding-box bottom reaches the final row.
- One-, two-, and three-cell connected objects remain fixed.
- In train 0 the two 2x2 objects have the same destination. Processing components
  in reading order makes the originally lower object overwrite the upper object's
  destination, matching the visible output.
- Train 1 moves the seven-cell staircase while keeping the two-cell domino fixed.
- Train 2 moves the four- and five-cell objects while preserving the one-, two-,
  and three-cell objects.

Implementation: find 4-connected components separately by color, erase all
components of size at least four, then place each at the bottom with no horizontal
shift. Components are placed in row-major discovery order, so later/lower movers
win any exact destination overlap.

Alternatives considered but rejected from the visible evidence:

- Move only the globally largest object: contradicted by train 2, where both the
  size-4 and size-5 objects move.
- Apply ordinary gravity to every object: contradicted by stationary size-1 to
  size-3 objects and by the missing upper 2x2 in train 0.
- Stop movers on other objects: no visible example requires that interaction; the
  chosen rule instead preserves fixed objects and lets movers overwrite only if a
  destination collision occurs.

Remaining uncertainty: the examples do not determine behavior for a moving object
whose destination overlaps a stationary small object, or for differently shaped
large objects with partial destination overlap. The implementation uses direct
placement, with movers written after stationary cells.
