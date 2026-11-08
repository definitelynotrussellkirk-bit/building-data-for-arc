# Solve work log

Earlier rule exposure: no. I had not opened this task's generator, Racket rule,
reference solution, private labels, notes, or audit evidence.

## Revision 1

The first two rows form a sparse vertical color legend, followed by a completely
blank separator row. Every nonzero color in the lower scene is replaced by the
color directly beneath it in the legend, while zero remains zero. The output is
only the lower scene, so the two legend rows and separator are removed.

Checks against the visible examples:

- Example 0 gives `2 -> 4`, `6 -> 8`, and `5 -> 3`.
- Example 1 gives `2 -> 1` and `7 -> 9`; colors 3 and 8 remain unchanged because
  they are scene details not listed as legend sources.
- Example 2 gives `9 -> 1`, `7 -> 5`, and `2 -> 8`; colors 3 and 4 remain unchanged.

Implementation locates the first all-zero row, reads the two preceding rows as
source/target pairs, then applies that mapping to the rows below the separator.
The main remaining assumption is that the public format always uses exactly two
legend rows immediately above the first blank row, which all three examples support.
