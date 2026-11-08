# Solve work log

Earlier exposure: yes. I had inspected the selected generator and canonical rule during the repair phase, so this is an exposed post-repair solve, not a blind solve. During this solve episode I used only the visible examples in `solve/README.md`; I did not reopen the generator, Racket source, reference solution, or private labels.

## Revision 1

All three examples contain three separated monochrome components. The output preserves each component's bounding-box crop, top-aligns the crops, and inserts one zero column between adjacent crops.

The output order is not input scan order, color order, bounding-box area, or occupied-cell count: the five-cell 3x2 crop precedes the five-cell 1x5 line even though its area is larger. Their bounding-box perimeters are 10 and 12, while the 2x2 block has perimeter 8, matching the output order 8, 10, 12 in every example. I therefore implemented 4-connected same-color extraction, bbox cropping, sorting by `(2*(height+width), left, top)`, and horizontal top-aligned packing with one-column gaps.

No failed natural revision was needed; the three visible examples directly separate the strongest size shortcuts.
