# Visible-only solve log

## Revision 1 — row qualification plus inclusive connection

The output has the same shape as the input. Each row is judged independently.
A row survives only when it contains exactly two nonzero cells and those two
cells have the same color. The output replaces that row by the inclusive
horizontal segment between those cells, using their color. Every other row is
cleared to zero, including:

- rows with two differently colored cells;
- rows with three nonzero cells even when an outer pair matches; and
- rows with a same-colored pair plus any additional nonzero marker.

Evidence from the visible examples:

- Train 0 joins `9 ... 9` and `6 . 6`; it clears the mismatched `9 ... 4`
  row and the three-cell `6 ... 4 6` row.
- Train 1 joins the two `8` markers in row 0, while the two-color row and
  the three-`8` row are cleared.
- Train 2 joins each exact same-color pair (`6`, `9`, `9`) and clears the
  three-cell and mismatched-pair rows.

Predictions implied for the two hidden queries:

- Query 0: row 0 becomes six `8`s; every other row is cleared. Row 2 has two
  `8`s but also a third `8`, so it is intentionally rejected.
- Query 1: only the row with exactly two `9`s qualifies; the row with three
  `3`s and the mismatched `5`/`3` row are cleared.

This is a human work log based only on the prepared visible examples. I had
already seen the canonical rule while reviewing the generator, so this is an
exposed post-repair solve, not a blind solve; I did not consult any reference
source or private label during this solve episode.
