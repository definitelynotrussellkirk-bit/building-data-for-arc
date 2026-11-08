# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or any audit evidence. I used only the visible
examples printed by `python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — symmetry-orientation hypothesis

The output preserves every object's cells and changes only its color. Repeated
shapes establish stable labels independent of input color: the vertically
symmetric A/T-like objects become 2; the horizontally symmetric six-cell object
becomes 3; diagonal or half-turn objects become 4; and odd 3×3 objects with both
horizontal and vertical symmetry (plus and ring) become 8.

A 2×2 square is the important parity clue: although it has both orthogonal
symmetries, both axes lie between rows/columns, and it is labeled 4 rather than
8. I therefore classify a component with both axes by bounding-box parity:
odd×odd -> 8, odd×even -> 3, even×odd -> 2, even×even -> 4. A sole vertical axis
maps to 2, a sole horizontal axis to 3, and diagonal/180-degree symmetry to 4.
Wholly asymmetric objects are left unchanged because the visible examples do
not define their class.

Before implementation I ran a direct visible-example probe against the supplied
stub and observed the expected `NotImplementedError`. The implementation uses
4-connected same-color components and compares normalized transformed cell sets.

Remaining uncertainty: query 0 contains a solid 3×2 rectangle. The parity rule
predicts 3 because its horizontal axis passes through the middle row while its
vertical axis lies between columns. This is the most constrained extension of
the square/odd-square evidence, but private query scoring is intentionally hidden.
