# Solve work log

## Exposure declaration before solving

This is the required post-repair solve, so I had already inspected and edited the
assigned generator earlier in the review. I therefore declare earlier exposure
as **yes**. During this visible-only solve I did not reopen the generator, Racket
rule, reference solutions, private query labels, or any previous solution
explanation. I used only the examples displayed by `python3 review.py solve
prepare` and the visible-only checker.

## Revision 1 — exact repeated component crop

**Hypothesis.** Treat every four-connected group of nonzero cells as an object.
For each object, take its complete axis-aligned bounding-box crop from the input,
including any zero cells enclosed by that box. Return the exact colored and
oriented crop that occurs more than once. The output is the crop itself, not a
recolored mask or a modified copy of the full canvas.

**Evidence from the visible examples.**

- Each output has the dimensions of one small object crop rather than the input
  canvas.
- In every training grid, the output appears twice as an exact colored array.
- Internal background cells in the crop are retained, so comparing only the set
  of nonzero coordinates would lose visible information.
- Other objects may share shape dimensions or colors, but they do not duplicate
  the complete colored crop in the same orientation.

**Alternatives considered.** A shape-only match would ignore color placement;
a rotation/reflection-normalized match would not explain why the output keeps
one exact orientation; selecting the largest or first object is contradicted by
the varied locations and distractor sizes. Exact array equality across component
bounding boxes accounts for all three examples with one rule.

**Implementation choices.** Components use four-connectivity because diagonal
contact does not visibly merge objects. Components are discovered row-major,
and the first crop with multiplicity greater than one is returned; the examples
show a single repeated crop family. The code preserves orientation, colors, and
internal zeros exactly.

**Remaining uncertainty.** The public examples do not show two distinct crop
families both repeated. The implementation assumes the puzzle construction has
one intended repeated family, as the examples consistently indicate.
