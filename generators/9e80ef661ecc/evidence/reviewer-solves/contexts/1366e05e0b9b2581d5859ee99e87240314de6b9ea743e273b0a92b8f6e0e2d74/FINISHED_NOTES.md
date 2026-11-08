# Blind solve notes — task 9e80ef661ecc

## Visible-only hypothesis
Each monochromatic 4-connected nonzero object is recolored according to the
number of 4-connected background regions enclosed by that object's shape. The
visible mapping is 0 holes → 2, 1 → 3, 2 → 4, 3 → 6, and 4 or more → 9.

Evidence: the small first example contains a solid square, one-hole ring, and
two-hole mask; the second example separates equal-area 4×4 objects solely by
0/1/2 enclosed regions. A scratch connected-component/flood-fill probe matched
all four visible outputs, including the larger-example categories. The two
queries contain only 0-, 1-, and 2-hole objects.

Implementation plan: segment by original color and 4-connectivity, count holes
in a one-cell-padded local mask, then recolor only the object's cells. Other
colors are ignored while measuring a shape so touching differently colored
objects remain distinct.
