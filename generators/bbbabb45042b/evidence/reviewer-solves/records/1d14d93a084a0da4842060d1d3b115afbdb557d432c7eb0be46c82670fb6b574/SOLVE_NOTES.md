# Blind solve notes — bbbabb45042b

This is a human work log based only on `challenge.json` and local Python reasoning.
No generator, Racket rule, reference output, prior explanation, or audit record was consulted.

## Hypothesis 1

Color 2 supplies a stencil and every color-1 cell is a placement anchor.  Normalize
the relevant color-2 object to its bounding-box top-left, recolor it 1, and place it
at every existing 1.  The anchor itself remains 1, so `(0, 0)` is always in the
placed pattern even when the stencil lacks that cell.

The second training example clarifies which color-2 cells form the stencil: there
is an isolated color-2 cell plus a four-cell connected object.  Copying all five
cells would produce a 4x3 pattern and does not match the output; selecting the
largest 4-connected color-2 component, normalizing it, and unioning the anchor
produces exactly `[[1,1],[0,1],[1,1]]`, which is repeated at all three 1 markers.

Checks against the other examples:

- Training 1: normalized T is `.1./111`; unioning the anchor gives `11./111`.
- Training 3: normalized zigzag already contains `(0,0)`; two overlapping copies
  exactly explain the eight output cells.
- Test 1 should stamp `11./111` at each of three anchors.
- Test 2 should stamp `11/.1/11` at each of three anchors.

Implementation uses deterministic 4-connected components and chooses the largest.
Generated placements appear designed to fit; bounds checks make the solver safe
without changing visible behavior.
