# Solve work log

This replacement assignment uses the same blind task as an earlier workspace that
was lost between execution environments. In that earlier attempt I saw a different
set of visible examples and inferred the bar transformation, so **earlier exposure
is yes**. I still did not inspect this task's generator, Racket rule, private labels,
reference solution, or audit history. This revision was checked against only the
new visible examples.

## Revision 1 — factorized cyclic rotation

The four bottom-aligned bars can be represented by left-to-right color and height
vectors. All three new demonstrations confirm the same factorization observed in
the earlier visible-only solve:

- colors rotate one position to the right;
- heights rotate one position to the left;
- bar columns, grid shape, background, and bottom alignment stay fixed.

For example 0, input colors `[6,1,2,5]` become `[5,6,1,2]`, while heights
`[8,7,6,4]` become `[7,6,4,8]`. Example 2 independently gives colors
`[4,8,6,9] -> [9,4,8,6]` and heights `[2,6,8,9] -> [6,8,9,2]`.

The implementation identifies the dominant background and every active column,
then draws output bar `i` with the color from bar `i-1` and height from bar `i+1`,
cyclically. The visible domain contains one solid color per bar and bottom alignment;
behavior outside that domain is intentionally not invented.
