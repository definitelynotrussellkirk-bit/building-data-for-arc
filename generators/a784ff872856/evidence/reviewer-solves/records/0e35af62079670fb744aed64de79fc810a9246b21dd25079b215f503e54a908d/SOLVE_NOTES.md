# Solve work log

I had not opened this task's generator, Racket rule, reference solutions, private
labels, audit records, or any earlier solution explanation before this solve.
I used only the visible presentation created by `review.py blind prepare`.

## Revision 1 — crop, order by width, and stack

Across all three training examples, the nonzero cells form three monochrome
objects with bounding-box widths 4, 2, and 1.  The output preserves each object's
cropped pixels without rotation or recoloring, orders the crops from widest to
narrowest, left-aligns them in a canvas whose width is the maximum object width,
and inserts one blank row between adjacent crops.  This explains the 10×4
training outputs: heights 2 + 3 + 3 plus two separator rows.

I wrote a visible-example regression script at
`WORK/checks/test_blind_solution_visible.py` before implementing the rule.  It
failed on the untouched `NotImplementedError` as expected (`blind-red.log`).  I
then implemented the rule generically by grouping nonzero cells by color,
constructing each color's bounding-box crop, sorting by decreasing width, and
stacking with zero-row separators.

The first query contains widths 4, 3, 2, and 1, so this hypothesis predicts a
13×4 output.  The second query has the demonstrated widths 4, 2, and 1 and thus
predicts a 10×4 output.  Remaining uncertainty: the examples do not define a
semantic tie-break for equal widths or show two disconnected objects sharing a
color.  The program uses original top/left position and then color only as a
deterministic tie-break, without claiming that tie behavior is established.
