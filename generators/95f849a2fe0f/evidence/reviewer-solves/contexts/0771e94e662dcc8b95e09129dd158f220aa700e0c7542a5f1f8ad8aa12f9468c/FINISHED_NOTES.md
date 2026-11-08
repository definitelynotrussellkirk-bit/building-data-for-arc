# Blind solve work log — 95f849a2fe0f

Earlier task-rule exposure: no. Reference consulted during this phase: no.
Only the prepared public examples and query inputs were inspected.

## Revision 1

Each example contains one red and one green four-cell shape. Crop each color
to its own upper-left bounding-box origin, align those origins, and take the
symmetric difference of occupied positions. Emit 8 at differing positions and
0 elsewhere, with the maximum of the two cropped heights and widths.

Manual checks: example 0 differs at (1,0) and (2,1); example 1 at (0,2) and
(1,0); example 2 at (0,3) and (1,1), all zero-based. These match all visible
outputs. Intersection and union would color different cells, so neither fits.
The solver treats the two observed foreground colors symmetrically.

One solution revision submitted. The public blind check completed and passed
all 3/3 visible examples; no failed solution revision occurred. This is enough
visible support to stop without inventing additional tests or changing the rule.
Hidden query correctness remains unknown; no private output was opened.
