# Solve notes

Earlier exposure: yes. I worked on this generator before preparation, so this is an exposed visible-example solve, not a blind solve. I did not consult the generator, Racket source, reference outputs, or private query labels after `solve prepare`.

## Hypothesis from the visible examples

1. Ignore background 0 and locate the signal color occurring exactly four times; the other two colors are distractors.
2. A row or column containing exactly two signal cells determines a full line in that signal color; all other cells are erased.
3. Exception for a complete 2×2-corner rectangle: draw only the two parallel lines aligned with the longer separation between corners. Thus a tall rectangle becomes two full columns and a wide rectangle becomes two full rows.
4. For non-rectangles, draw every qualifying pair row and pair column. This explains the one-row/two-column and two-row/one-column crosses in the visible examples.

The implementation also checks the four-cell color is supported on at most three rows and columns, and prefers the candidate with the most pair structure if an input contains more than one count-four color.
