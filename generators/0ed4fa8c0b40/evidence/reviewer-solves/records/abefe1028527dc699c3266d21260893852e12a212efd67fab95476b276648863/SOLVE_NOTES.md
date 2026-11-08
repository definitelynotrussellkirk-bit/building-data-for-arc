# Post-repair visible-only solve work log

I had already inspected this generator and its rule during the assigned repair,
so this attempt is **not blind**. During this solve phase I used only the visible
examples printed by `python3 review.py solve prepare`; I did not reopen the
Racket rule, generator, reference solution, or private query labels.

## Revision 1

The yellow five-cell marker has a three-cell horizontal bar, a stem below its
centre, and a single apex above either the left or right side. The apex's offset
from the bar centre chooses the side of the transformation. The cyan cells are
kept, and a horizontally reversed copy is painted immediately beyond the chosen
vertical edge of the cyan bounding box.

For a right-pointing arrow and cyan columns `[left, right]`, a source column `c`
lands at `2*right + 1 - c`. For a left-pointing arrow it lands at
`2*left - 1 - c`. This explains the sparse holes in examples 0–2 and the dense
rectangle in example 3; a simple translation would disagree on the asymmetric
supports.

Predictions:

- query 0 points right, so the 3-column cyan support at columns 3–5 is reflected
  into columns 6–8;
- query 1 points left, so the support at columns 3–5 is reflected into columns
  0–2.

The program preserves the original grid and paints only the reflected cyan
cells. Remaining uncertainty is limited to malformed inputs with a non-unique
arrow; the prepared episode uses the demonstrated lawful grammar.
