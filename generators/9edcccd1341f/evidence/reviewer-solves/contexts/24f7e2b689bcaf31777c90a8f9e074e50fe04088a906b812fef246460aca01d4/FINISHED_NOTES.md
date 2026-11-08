# Solve work log

## Exposure declaration

This is a human work log. I had already reviewed this task's generator and Racket
rule before the post-repair solve, so earlier rule exposure is **yes**. During
this solve I kept those sources closed and used only the prepared visible
examples, `challenge.json`, my own Python, and visible-only checker feedback.

## Revision 1 — dominant interior color and its bounding rectangle

Across all three demonstrations, row 0 is copied unchanged and acts as a color
key. Rows 1 and the last row, plus the left/right sides below row 1, form a
uniform input frame. In the output that frame changes from its old color to the
most frequent nonzero interior color: 8 in example 0 and 1 in examples 1–2.
All other interior colors disappear.

The retained cells are not the dominant color's original shape. They are the
hollow perimeter of its axis-aligned bounding box. Example 0 turns the scattered
8s spanning rows 2–5 and columns 4–7 into that rectangle; examples 1 and 2 do
the same for color 1. Therefore the program:

1. preserves row 0;
2. counts nonzero interior colors while excluding the old frame color;
3. selects the unique most frequent color;
4. recolors the entire outer frame below the key with that color;
5. clears the framed interior and draws the selected color's hollow bounding box.

The two visible queries have a unique dominant interior color 3, so the same
rule is directly applicable. Remaining uncertainty is limited to malformed or
tied inputs not represented by the prepared episode; the generated examples
show a unique winner and a two-dimensional bounding box.
