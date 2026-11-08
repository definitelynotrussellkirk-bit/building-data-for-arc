# Blind solve: fa3e0c305476

Before this solve I read packet process documentation and the public challenge
only. I have not opened any generator, Racket rule, reference solution, canonical
labels, prior solution explanation, or audit evidence. No earlier rule exposure
is known. The separate documentation agent read process documents only.

## Hypothesis and visible probes

All objects are color 8 on zero background. Shape and zeros are preserved.
The first example (14 by 23 input and output) has an 8-cell one-hole object
recolored 1, a solid 4-cell object unchanged, and a 13-cell two-hole object
recolored 2. The second (11 by 20) has a four-hole 23-cell object recolored 7
and a three-hole 22-cell object recolored 3. Its three holes each contain two
cells: this distinguishes counting enclosed regions from counting zero cells.
The third (15 by 18) leaves five-hole and six-hole objects unchanged and again
maps a one-hole object to 1.

A visible-only Python flood-fill probe confirmed these component statistics:
example 0: (cells, holes, color) = (8,1,1), (4,0,8), (13,2,2);
example 1: (23,4,7), (22,3,3);
example 2: (28,5,8), (8,1,1), (29,6,8).

## Revision 1

Use orthogonal connected components of color 8. Count bounded connected
components of each object's complement in a padded bounding box. Recolor with
1->1, 2->2, 3->3, 4->7; otherwise retain 8. Preserve all other cells.
This uses topology and handles variable hole area, shape, translation and objects
touching the image border. I did not create a deliberately wrong solve revision.

## Limits and stopping criterion

Visible examples do not distinguish orthogonal from diagonal foreground
connectivity or show nested objects. The implementation chooses orthogonal
connectivity, supported by every shown object. Counts above six and other
foreground colors are untested; they remain unchanged. Query inputs are 14 by 19
and 11 by 21; their output dimensions and correctness remain unobserved.
I will stop after checking this hypothesis if all visible examples agree and
both query executions succeed; this is not a claim of masked-query correctness.
