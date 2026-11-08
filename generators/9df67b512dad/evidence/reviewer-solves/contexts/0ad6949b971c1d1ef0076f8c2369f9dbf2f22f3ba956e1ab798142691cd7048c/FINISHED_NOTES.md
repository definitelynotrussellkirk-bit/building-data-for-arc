# Solve work log

## Prior exposure

Before this blind episode I had not opened task `9df67b512dad`'s generator,
canonical rule, notes, solutions, labels, or audit records. I had only read the
packet-level instructions and assignment text. I did not know this task's rule.

## Attempt 1 — nine spatial regions with row-major overwrite

The outputs are always 3x3 although the inputs vary in size. I grouped every
input coordinate by whether its row is the first row, last row, or an interior
row, and independently whether its column is the first, last, or interior. This
maps the input onto nine regions: four singleton corners, four boundary strips,
and the whole interior.

A region can contain multiple colors. Across the examples, the output is the
last nonzero encountered in ordinary row-major order within that region:

- On a top or bottom strip this is the rightmost nonzero.
- On a left or right strip this is the lowest nonzero.
- In the interior it is the lowest row's rightmost nonzero.
- An empty region remains zero.

Checks against ambiguous examples: the second training interior ends in color 3;
the third training top/interior/bottom strips end in color 9; and the fourth
training edge strips end in color 3. These distinguish overwrite order from
plain plurality. I implemented this directly by scanning the grid and replacing
the corresponding 3x3 cell for each nonzero.

Predicted tests before checker feedback:

1. `[[0,7,4],[7,7,7],[4,7,0]]`
2. `[[4,0,4],[4,4,4],[4,0,4]]`

Remaining uncertainty: the examples establish row-major last-write behavior for
all non-corner region types, but not a case with two colors in the same final
coordinate (which cannot occur in a grid anyway).
