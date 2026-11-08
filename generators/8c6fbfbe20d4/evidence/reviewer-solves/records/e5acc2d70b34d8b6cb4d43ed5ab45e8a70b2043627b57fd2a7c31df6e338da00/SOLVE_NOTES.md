# Solve notes

Earlier exposure: yes. I reviewed this task's generator semantics before this
post-repair solve, so this is not blind and I do not use it as independent rule
discovery evidence.

Visible-example check:

- The first two rows disappear from every output.
- Reading nonzero values left-to-right gives two ordered color lists.
- Pair source list entries from row 0 with target list entries from row 1 only
  up to the shorter length.
- Recolor matching body cells in rows 2+ and preserve zeros and every other
  value.

Example 1 gives 2→3, 9→6, 7→5 while leaving the extra row-1 value 1 unused.
Example 3 gives 5→7, 4→2, 6→8 and preserves neutral 1. Those checks reject
same-column matching, sorted-color matching, and erasing non-header values.

Implementation: extract both sparse lists, build `dict(zip(sources, targets))`,
then map rows 2+ with identity fallback.
