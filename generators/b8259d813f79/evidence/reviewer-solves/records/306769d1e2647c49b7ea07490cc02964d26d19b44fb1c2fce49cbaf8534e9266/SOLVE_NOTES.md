# Solve work log

## Exposure declaration

Before this solve I had read only the packet-level instructions and the visible
presentation created by `blind prepare`. I did not open any generator, Racket
rule, canonical answer, prior solution, or audit evidence for this task.

## Revision 1 — connected-object bounding-box centers

### Observation

Each input contains several separated, single-color 4-connected objects. Each
output keeps the original canvas size, removes every object, and leaves exactly
one pixel of that object's color.

For every visible object, that pixel is at the integer center of the object's
axis-aligned bounding box, with floor/upper-left bias when a dimension is even:

- Train 0, color 7: bounding box rows 0..2, columns 6..8 -> (1, 7).
- Train 1, upper color 2: rows 0..1, columns 0..3 -> (0, 1). This
  distinguishes floor midpoint from rounding the centroid, which would not
  explain the shown output reliably.
- Train 1, lower color 2: rows 4..6, columns 2..4 -> (5, 3), even though that
  center cell is background in the input. Thus the rule is not "retain a
  central occupied cell."
- Train 2, upper-right color 2: rows 1..2, columns 6..9 -> (1, 7).

### Alternatives considered

- **Centroid/center of mass:** rejected by the upper color-2 object in Train 1;
  its geometric centroid is near column 1.8 while the output uses column 1,
  exactly the floored bounding-box midpoint.
- **Median occupied coordinate:** also predicts a different column for that
  object.
- **One marker per color rather than per object:** rejected because Train 1 has
  two objects of each color and outputs two markers of each color.
- **8-connectivity:** unnecessary for the shown objects; 4-connectivity is the
  standard conservative object definition and keeps diagonally touching shapes
  distinct if encountered.

### Implementation

Scan every nonzero 4-connected same-color component, compute its min/max row and
column, and write its color at `((min_row + max_row)//2,
(min_col + max_col)//2)` on a zero canvas of the same shape.

### Remaining uncertainty

The examples do not explicitly show diagonally touching same-color objects or
nonzero background. I use 4-connectivity and color 0 as background because both
match all visible examples and standard ARC conventions for separated objects.
