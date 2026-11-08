# Solve notes

The three visible examples share one invariant: row 0 contains exactly one
nonzero cell. Its color is preserved at that top-row position, while every cell
of the same color in later rows is changed to 0. All other colored cells retain
their positions and values.

Checks against the examples:

- Example 0 selects color 4; only the body 4 at row 4 is erased.
- Example 1 selects color 5; the two body 5 cells are erased and the top-left 5
  remains.
- Example 2 selects color 6; the three body 6 cells are erased and the top-row 6
  remains.

Rejected alternatives: erase the most frequent body color (examples 0 and 2
contradict it), erase a fixed color, erase the color in the marker column, and
erase the top marker too. The implementation therefore finds the unique
nonzero top-row color and removes matching cells only from rows 1 onward.
