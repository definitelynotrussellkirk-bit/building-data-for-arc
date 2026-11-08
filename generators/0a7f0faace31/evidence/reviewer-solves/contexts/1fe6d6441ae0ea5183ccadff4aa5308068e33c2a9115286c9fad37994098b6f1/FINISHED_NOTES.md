# Solve work log

I had no earlier exposure to this task's generator, Racket rule, reference solution,
private labels, or prior solve notes. I used only the visible challenge.

## Revision 1 — rightmost monochromatic object

Observation: every example has several colored motifs on background color 5 and a
single-cell decoy just beyond the desired motif. The output is a tight crop of the
rightmost **non-singleton monochromatic 4-connected component**, preserving every
original cell inside that component's bounding box (including holes and a differently
colored interior pixel).

I compared alternatives before coding:

- Treating all non-background colors as one component fails because nearby motifs of
  different colors touch orthogonally.
- Eight-connectivity fails because the right-edge singleton is diagonally adjacent to
  the target in the first two examples.
- Selecting the rightmost nontrivial same-color 4-component matches all three visible
  pairs: the selected bounding boxes are 3x4, 3x4, and 3x3 respectively.

Implementation: infer the background as the modal color, enumerate same-color
4-connected components, discard size-one components, choose the component with the
largest rightmost column, and crop its bounding box from the unmodified input.
Ties are broken by component size and then deterministic bounding-box order; no visible
example exercises a tie. Remaining uncertainty is whether an unseen case can contain a
non-singleton distractor farther right than the intended object.
