# Visible-only solve notes

This is a human work log written after generator review, so earlier exposure to
the family rule is **yes**. During this solve phase I used only the prepared
visible challenge and my own Python implementation; I did not reopen the Racket
rule, generator, reference solution, private labels, or earlier solve records.

## Hypothesis

Each nonzero cell other than the unique color-2 cell is a marker. Select the
row-extreme and column-extreme markers: topmost, bottommost, leftmost, and
rightmost. Their row/column coordinates define a rectangle, and their colors
paint its top, bottom, left, and right edges. Build the output from a zero grid,
then draw a color-5 horizontal and vertical arm through the color-2 center.

The visible examples establish precedence. Top and bottom edges win at corners;
left then right are considered after them. The frame also wins over the center
and cross: in train example 1 the center lies on the bottom edge and becomes the
bottom marker's color. The center is otherwise color 2 and the interior arm
cells are color 5. Train example 2 contains an interior non-extreme marker that
is erased. Query 0 shows one marker can serve both top and left roles.

## Probe before revision 1

I checked the inferred coordinates manually:

- Train 0: bounds rows 3..18 and columns 2..12, center (17,7).
- Train 1: bounds rows 2..11 and columns 1..12, center on bottom row (11,8).
- Train 2: bounds rows 4..12 and columns 1..10; the extra 7 at (8,3) is ignored.
- Train 3: bounds rows 1..10 and columns 5..11, center (8,6).

All four visible outputs follow the same reconstruction and precedence, so I
implemented the general rule directly. There were no accidental failed
revisions or deliberate teaching negatives.
