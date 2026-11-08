# Solve work log

I had earlier exposure to the task's intended rule while repairing its generator,
so this is an exposed post-repair solve, not a blind solve. During this solve I
used only the freshly prepared visible examples and did not reopen the generator,
Racket source, private labels, prior solution explanations, or reference answers.

## Revision 1

The visible inputs each contain two structures on background 0:

1. a large repeated-color shape made of equal square blocks; and
2. a dense 3x3 or 4x4 palette containing mostly singleton/repeated colors.

The output has the palette's dimensions. Comparing each training output with its
palette suggests a coordinate-wise mask: retain palette cell `(r,c)` exactly when
the corresponding large block is filled, otherwise write 0.

Implementation plan:

- choose the most frequent nonzero color as the large-shape color;
- locate the palette from the bounding box of nonzero cells of other colors;
- exclude that palette box before finding the large shape, since a palette cell
  may reuse the shape color;
- divide the large shape's bounding box into the palette's row/column count;
- use occupancy of each block to mask the corresponding palette entry.

The main alternative considered was outputting the large block pattern itself or
using palette colors merely as a set. Both are contradicted by the positional
palette values in the three visible examples. Remaining uncertainty is limited
to malformed inputs outside the visible family; the parser assumes the palette
contains enough non-shape cells to reveal its full square bounding box.
