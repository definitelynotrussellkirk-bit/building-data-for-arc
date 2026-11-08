# Solve work log

## Exposure

Before this blind step I had read only the packet-level directions and the visible
examples produced by `python3 review.py blind prepare`. I did not inspect this
task's generator, Racket rule, reference solution, private query labels, audit
records, or prior solution notes.

## Revision 1 — orientation-sensitive template matching plus reflection

The input contains one blue (`1`) connected object and several green (`3`)
objects. I normalized every 4-connected object by its top-left corner and compared
shapes without rotation or reflection. The outputs retain only green objects whose
normalized pattern exactly equals the blue pattern in the same orientation.
Mirrored green distractors are omitted.

The retained object's output is not merely its original cells. It is the union of
the matching object and its left-right reflection inside the same bounding box,
painted azure (`8`), on an otherwise blank grid:

- examples 0 and 1 turn the two opposite zig-zag variants into a full `3 x 2`
  rectangle only for copies matching the blue orientation;
- example 2 turns a matching L triomino into a full `2 x 2` square, while rejecting
  the horizontally mirrored L;
- example 3 is the decisive probe: a `2 x 3` four-cell pattern becomes a five-cell
  pattern with both top corners and the full bottom row. That is exactly the union
  with its horizontal reflection, not a filled bounding rectangle.

Implementation: identify the largest blue component as the template, find green
4-connected components, keep exact normalized matches, and paint each source cell
and its column reflection around the component bounding box as `8`. All other cells
become `0`.

Remaining uncertainty: the visible examples contain one blue component and use
4-connectivity. The largest-blue fallback is defensive rather than inferred, and
there is no evidence for diagonal connectivity or multiple template objects.
