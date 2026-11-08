# Fresh visible-example solve notes

This is a human work log based only on `solve/challenge.json`. I had already
seen the task rule during the assigned generator review, so this episode is not
blind; I did not reopen the generator, Racket source, reference solutions, or
private labels while solving.

## Hypothesis

Each nonzero monochromatic 4-connected component is an independent object.
Tight-crop every component, sort objects by their leftmost input column, break a
tie by top row, and stack the crops top-to-bottom. Use the widest crop as output
width, left-align narrower crops, and insert one all-zero separator row.

Visible evidence:

- The first example orders colors 7, 6, 8 by increasing left edge rather than
  by color or top row.
- The second and third examples show unequal crop widths and left alignment.
- The fourth example has colors 6 and 4 with the same left edge; the higher
  object (6) appears first, exposing the top-row tie break.
- The fifth example has two disconnected color-3 components; they remain two
  objects rather than being merged by color.
- Every consecutive output crop is separated by exactly one blank row.

## Implementation

Scan row-major, flood-fill same-color 4-neighbors, build masked tight crops,
sort by `(left, top)`, then concatenate with separators and right padding. This
is deliberately component-based so disconnected objects of one color remain
separate.
