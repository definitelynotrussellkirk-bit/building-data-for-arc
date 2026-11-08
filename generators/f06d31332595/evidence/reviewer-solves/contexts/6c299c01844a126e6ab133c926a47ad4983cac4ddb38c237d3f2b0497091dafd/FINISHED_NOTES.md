# Blind solve notes — f06d31332595

This is a human work log based only on the visible examples printed by the packet.
No generator, canonical rule, private answer, prior solution, or audit evidence was consulted.

## Hypothesis

Every input contains one full-height vertical column of color 5. The output keeps the
input unchanged and mirrors every nonzero cell strictly to the left of that column onto
the corresponding location on the right. For axis column `a`, source column `c` maps to
`2*a-c`; colors and row positions are preserved. Background cells are not copied.

Checks against the examples:

- Example 0: axis 4; `(2,0)` maps to `(2,8)`, `(1,3)` to `(1,5)`, and `(4,2)` to `(4,6)`.
- Example 1: axis 6; the adjacent cells at column 5 map to 7, and cells at columns 0, 1,
  and 2 map to 12, 11, and 10.
- Example 2 shows multi-cell colored runs mirrored without reversal beyond geometric
  reflection (the reflected row pattern is the horizontal mirror image).

The implementation locates exactly one all-5 axis column, copies the grid, and writes the
reflected nonzero left-side cells. The visible examples do not require modifying cells on
the right or handling a horizontal axis.
