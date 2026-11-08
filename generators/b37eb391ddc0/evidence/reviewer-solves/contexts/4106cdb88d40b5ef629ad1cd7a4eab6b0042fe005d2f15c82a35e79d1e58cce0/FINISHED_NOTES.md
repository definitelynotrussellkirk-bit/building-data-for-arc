# Blind solve notes

## Initial observations

Each training input contains one five-cell, 8-connected cluster plus isolated distractors.
Within that cluster, one color occurs three times and the other occurs twice.  The
three occurrences of the majority color occupy alternating cells of a 2x3 rectangle
(or, by symmetry, a 3x2 rectangle).  The output fills that rectangle with the
three-occurrence color.  One minority-color cell lies inside the rectangle and is
overwritten; the other lies just outside and is preserved.  All isolated cells are
preserved.

Examples:

- Train 0: color 4 has bounding box rows 4-5, columns 4-6; fill it with 4.
- Train 1: color 4 has bounding box rows 4-5, columns 5-7; fill it with 4.
- Train 2: color 5 has bounding box rows 3-4, columns 1-3; fill it with 5.

## Implemented hypothesis

Find 8-connected nonzero components.  Select the unique five-cell component whose
color counts are 3 and 2 and whose three-cell color has a 2x3/3x2 bounding box with
all three clues on one checkerboard parity.  Fill that bounding box with the
three-cell color and leave the rest unchanged.

This predicts query 0 fills rows 2-3, columns 3-5 with color 3, and query 1 fills
rows 2-3, columns 3-5 with color 1.
