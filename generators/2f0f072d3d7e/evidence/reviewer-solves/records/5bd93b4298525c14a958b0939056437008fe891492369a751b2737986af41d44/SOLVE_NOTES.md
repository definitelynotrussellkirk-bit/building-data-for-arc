# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private
labels, audit evidence, or prior solution explanation. Before solving I saw only
the packet's generic instructions, the assignment task IDs, and the visible
examples emitted by `python3 review.py blind prepare`.

## Revision 1 — visual analogy by a dihedral transform

The 4×29 input separates into six 4×4 panels at the five all-9 divider columns.
The first two panels contain the same polyomino in different orientation and
position. The third panel is a new source shape, and panels 4–6 are three answer
choices. The output is one answer choice, recolored 8 while retaining that
choice's 4×4 placement.

I stripped color, cropped each shape to its occupied bounding box, and enumerated
the eight rotations/reflections. On the five demonstrations, the first-to-second
transform was respectively a 90° clockwise rotation, a 90° counter-clockwise
rotation, a 90° clockwise rotation, a 90° counter-clockwise rotation, and a
left-right reflection. Applying the same transform to the cropped third panel
selected exactly the demonstrated choice each time. The displayed placement of
the matching choice, rather than a newly centered transformed crop, reproduces
the output.

A local visible-example harness initially failed on the supplied
`NotImplementedError`, then passed all five demonstrations after implementing
this rule. The implementation keeps all transforms consistent with a symmetric
reference shape and requires their candidate matches to identify one unique
choice; otherwise it raises instead of silently guessing.

Remaining uncertainty: private queries are not scored here. Both visible queries
have a unique match: query 0 uses a 180° rotation and selects the first choice;
query 1 uses a 90° clockwise rotation and also selects the first choice.
