# Solve notes

## Revision 1

The transformation is row-local and shape-preserving.

For each row, ignore background 0 and marker 9, then count the **distinct**
remaining colors:

- exactly one distinct companion color and at least one 9: replace every 9 in
  that row with the companion color;
- zero companion colors: leave the 9s unchanged;
- two or more companion colors: leave the 9s unchanged.

Evidence from the visible examples:

- Train 0 and 2 show one or several copies of a single companion color, with
  the row's 9 changed to that color.
- Train 1 row 4 contains only 9s, so it stays unchanged.
- Train 1 final row contains colors 1 and 5 plus 9s, so it stays unchanged.
- Train 1 qualifying rows have multiple 9s, and all of them change, ruling out
  a first-marker-only rule.

Query 0 deliberately contains all three row types, so the row predicate can be
applied independently. Query 1 contains only qualifying rows plus blanks.
