# Blind solve notes — a4f0ea66fd65

This is a human visible-example work log. I did not inspect any generator,
canonical rule, private answer, prior solution, or audit evidence.

## Observations

- Every example contains a color-8 motif, one color-2 marker, and one color-3 marker.
- Example 0: the vector from 2 at `(0,5)` to 3 at `(2,8)` is `(2,3)`.
  Translating the five 8-cells by `(2,3)` gives exactly the five new color-1 cells.
- Example 2 independently gives vector `(2,-3)` and the translated 8-motif again
  matches every new color-1 cell.
- Example 1 uses vector `(-4,0)`. Two translated cells land on color 7 and replace
  them, explaining why the count of color 7 falls from four to two.
- Example 3 also demonstrates overwrite behavior: two translated cells land on
  color 7 and become color 1.

## Hypothesis

Copy every color-8 cell by the displacement vector `position(3) - position(2)`.
Paint the translated copy color 1, overwriting any existing cells. Leave the
original motif and all other cells unchanged except at translated destinations.

## Query predictions

- Query 0: displacement `(4,-1)`; paint `(10,7)`, `(11,6)`, `(11,7)`,
  `(12,5)`, `(12,6)`, `(12,7)` color 1.
- Query 1: displacement `(2,-3)`; paint `(3,5)`, `(4,5)`, `(5,5)` color 1,
  overwriting two color-7 cells.

## Implementation notes

The solver copies the input, locates markers 2 and 3, records all color-8 cells,
and applies the displacement. It clips translated coordinates defensively, though
all visible lessons keep the copy in bounds.
