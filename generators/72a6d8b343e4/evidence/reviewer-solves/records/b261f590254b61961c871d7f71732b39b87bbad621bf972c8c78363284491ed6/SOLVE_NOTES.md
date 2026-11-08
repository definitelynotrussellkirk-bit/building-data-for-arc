# Visible-only solve notes

This is a human work log written after generator repair, so earlier rule exposure
is **yes**. During this solve episode I consulted only `solve/challenge.json` and
used no Racket source, generator source, private labels, or prior solution text.

## Hypothesis

Group nonzero cells by colour. A colour changes only when it has exactly two
occurrences and those two cells share a row or a column. In that case paint the
inclusive straight segment between them. Adjacent aligned cells are already a
complete segment. Misaligned two-cell groups and groups with three occurrences
remain unchanged.

Evidence from the visible examples:

- Train 1 bridges horizontal colour 4 and vertical colour 5.
- Train 2 bridges aligned colours 8 and 2, but leaves the three colour-1 cells
  and misaligned colour-3 pair unchanged.
- Train 3 fills the one-cell gap between colour 3; adjacent colour 5 is unchanged.

The first implementation directly encodes this rule. No failed revision was
needed because all three visible examples distinguish both relevant guards.
