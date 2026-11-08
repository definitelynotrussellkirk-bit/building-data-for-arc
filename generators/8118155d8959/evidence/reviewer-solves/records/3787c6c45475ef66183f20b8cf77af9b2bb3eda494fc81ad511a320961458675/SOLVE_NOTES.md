# Solve work log

Earlier exposure: none. I had not opened task 8118155d8959's generator, rule,
notes, reference solutions, audit evidence, or private labels before this solve.

## Revision 1

Hypothesis: only the color-1 objects change. There are exactly three 4-connected
color-1 components in every visible example, with three distinct areas. Sorting
them by area maps smallest -> 2, middle -> 3, largest -> 8; all other cells stay
unchanged.

Evidence from the visible examples:

- Example 0 has component areas 3, 4, 5 and outputs colors 2, 3, 8.
- Example 1 has component areas 2, 3, 4 and outputs colors 2, 3, 8.
- Example 2 has component areas 2, 4, 5 and outputs colors 2, 3, 8.
- The same tetromino shape receives different output colors in examples 0 and 1,
  ruling out a shape-only classification. The area rank is consistent instead.
- The already-colored middle objects are unchanged and appear to be distractors.

Implementation: find all 4-connected components of value 1, require exactly
three distinct sizes, sort by size, and recolor them 2/3/8. I kept the guard so
unsupported inputs fail loudly rather than silently inventing an ordering.

Remaining uncertainty: the hidden queries might contain ties or a different
number of components, but both visible queries also show exactly three components
with distinct areas, so the inferred contract applies directly.
