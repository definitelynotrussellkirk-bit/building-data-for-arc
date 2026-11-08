# Solve work log

## Prior exposure

Before this solve I read only the packet-level instructions and the visible challenge prepared by `review.py blind prepare`. I did not open any generator, Racket rule, canonical rule, task notes, audit evidence, reference solution, or private label for this task.

## Revision 1 — header selects object, transform, and output color

The input is a 2×2 arrangement of colored objects. The first four cells of the header contain a unary run of color 1 whose length is 1–4. Across the five examples those lengths select the top-left, top-right, bottom-left, and bottom-right object respectively. Header column 5 contains a small integer controlling orientation, and column 7 contains the output color.

Visible transform evidence:

- code 1 leaves the chosen object unchanged;
- code 2 rotates it 90° clockwise;
- code 3 rotates it 180°;
- code 4 rotates it 90° counter-clockwise;
- code 5 reflects it left-to-right.

I wrote a temporary visible-example regression test before implementation. It failed on the original `NotImplementedError`, as expected. The solver now crops the selected panel to its nonzero bounding box, applies the observed transform, and recolors every occupied cell with the final header color. I intentionally do not guess codes beyond the five demonstrated ones; both test queries use demonstrated codes 1 and 2.

Predicted query behavior:

- query 0: select the top-right object, keep its orientation, recolor it 8;
- query 1: select the bottom-left object, rotate it clockwise, recolor it 8.

Remaining uncertainty: the fixed panel/header layout is strongly supported by every visible example, but no visible case demonstrates transform codes above 5.
