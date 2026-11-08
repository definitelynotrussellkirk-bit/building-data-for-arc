# Blind solve notes

## Hypothesis

Color `9` is a one-cell motion marker placed on exactly one outer border. Remove
that marker, then translate every other nonzero cell by one cell toward the same
border while preserving colors, shapes, and grid dimensions.

Evidence:

- Example 0: top-border 9; all objects move up one row.
- Example 1: bottom-border 9; all objects move down one row.
- Example 2: left-border 9; the object moves left one column.
- Example 3: right-border 9; the object moves right one column.

The two queries therefore use an upward shift (query 0) and a downward shift
(query 1). The implementation deliberately rejects malformed cases with no
unique border marker or an object that would be shifted out of bounds.
