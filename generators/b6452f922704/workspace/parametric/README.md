# Spatial versus largest-overlap-first gallery order

The canonical setting preserves the exact selected Racket program: construct a
key-colored rectangle from each frame's red/blue bounding-box overlap and pack
the three rectangles in spatial frame order.

The alternate setting computes those same three local overlap rectangles,
selects the unique largest overlap, and cyclically rotates the gallery so that
selected frame appears first.  The first two demonstrations put the anchor at
different spatial indices and deliberately make cyclic order differ from global
area sorting.

Sequential dependency:

1. **A** computes the three input-dependent overlap rectangles and selects the
   unique largest one.
2. The intermediate is its spatial frame index plus the ordered part records.
3. **B** uses that index to rotate the part list before vertically centered
   packing.

The family supports 2–6 demonstrations, 1–4 independently revealable queries,
matched inputs across settings, and a boundary-spanning 30×30 query.
