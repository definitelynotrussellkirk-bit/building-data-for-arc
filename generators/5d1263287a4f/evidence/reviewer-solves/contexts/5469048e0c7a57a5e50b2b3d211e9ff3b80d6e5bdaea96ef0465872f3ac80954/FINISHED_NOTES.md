# Solve work log

## Exposure declaration

Before this solve I had not opened the task's generator, Racket rule, canonical
record, prior solution, audit evidence, or private labels. I used only the visible
examples printed by `review.py blind prepare` and `challenge.json`.

## Revision 1 — split into three horizontal panels

The training inputs all have width 9 and outputs have width 3. Splitting each
input into three equal vertical panels shows that the output is exactly the
leftmost panel. The later panels may be identical to it or horizontally mirrored:

- example 0: original, original, mirror;
- example 1: original, original, original;
- example 2: original, mirror, mirror.

I checked the variable-width query rather than assuming a fixed three-column
crop. Query 0 has width 12, so its three panels are width 4; all three width-4
panels are identical. Query 1 has width 9; its second and third width-3 panels
are mirrors of the first. This supports the general rule “return the first of
three equal-width panels,” not “return the first three columns.”

The implementation validates a rectangular input whose width is divisible by
three, computes `width // 3`, and copies that many leftmost cells from each row.
A remaining uncertainty is whether the intended verbal story is “recover the
unflipped original” rather than simply “take the first panel,” but every visible
case explicitly places that original first, so the executable transformation is
the same on the observed domain.
