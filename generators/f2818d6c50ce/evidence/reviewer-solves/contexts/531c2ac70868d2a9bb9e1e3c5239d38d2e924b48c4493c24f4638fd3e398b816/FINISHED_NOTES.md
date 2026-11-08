# Post-repair solve notes

This is an exposed solve from visible examples only. I had already reviewed the
selected task's generator and rule before this episode, so earlier rule exposure
will be recorded as **yes**. During this solve phase I did not reopen the
generator, Racket source, private labels, or reference explanations.

## Visible-example hypothesis

Group nonzero cells by color. Only colors appearing exactly twice contribute an
output row. For each exact pair, measure the inclusive span

`max(abs(row1-row2), abs(col1-col2)) + 1`.

Sort those lengths ascending. The output has one row per retained color and the
maximum length as its width; each row is a left-aligned run of color 8 padded by
zeros.

Evidence from the three visible demonstrations:

- Demo 1 exact-pair lengths are 3, 6, and 7, matching the three output rows.
- Demo 2 contains a singleton color 2, which is absent from the output. The four
  exact-pair lengths are 2, 3, 6, and 11.
- Demo 3 contains a three-cell color 1 and singleton color 6; both are ignored.
  Exact-pair lengths are 3, 10, 10, 11, and 14, including the repeated bar.

## Revision 1

Implemented the exact-pair filter, inclusive Chebyshev length, ascending sort,
and color-8 bar construction. This also predicts that a one-pair query should
produce a single solid row rather than treating a singleton distractor as a
pair.
