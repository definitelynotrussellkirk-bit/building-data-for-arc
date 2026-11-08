# Blind solve notes — d7b84df5a06a

I used only `solve-blind/challenge.json` and did not inspect any generator,
reference rule, solution, audit, or private label.

## Hypothesis

The full row and column of color 5 partition the grid into four rectangles.
Within each rectangle, count marker colors 2, 3, and 4. Replace every zero in
that rectangle by:

- 6 when color 2 has the unique largest count;
- 7 when color 3 has the unique largest count;
- 8 when color 4 has the unique largest count;
- 9 when the largest count is tied.

Preserve the marker cells and the color-5 divider.

## Evidence from the visible examples

Every training example has exactly one quadrant receiving each of 6, 7, 8, and
9. In the first example, the four marker-count triples `(n2,n3,n4)` are
`(0,2,1)`, `(1,1,2)`, `(1,1,1)`, and `(2,0,1)`, matching fills 7, 8, 9, and 6.
The other two examples agree: unique majorities for 2/3/4 map to 6/7/8 and a
maximum tie maps to 9.

## Implementation choices

The solver locates the unique complete divider row and column rather than
assuming their indices. It copies the input, changes only zeros inside the four
rectangles, and rejects malformed inputs without exactly one divider row and
column. The visible data does not establish behavior for an empty rectangle;
the implementation treats `(0,0,0)` as a tie and therefore fills it with 9.
