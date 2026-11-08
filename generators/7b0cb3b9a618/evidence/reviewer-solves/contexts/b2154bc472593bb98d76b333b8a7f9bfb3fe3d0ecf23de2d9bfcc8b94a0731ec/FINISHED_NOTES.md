# Solve notes

## Revision 1 — crossing bands, clean row first

From the visible examples only:

- Training 1 contains a full nonzero row of color 1, and the output is `[[1]]`.
- Training 3 contains two full nonzero rows of color 6, and the output is `[[6]]`.
- Training 2 has no full nonzero row. Its top row is `[6, 2, 6]`: the first value 6 is the strict row majority and 2 is the single anomaly, matching output `[[2]]`. The anomaly is also the uninterrupted vertical stripe.

Hypothesis: scan for a uniform nonzero row and return its color. If none exists, find a nonzero-first row with exactly one value different from its first/major color and return that anomaly. This is consistent with a last-painted horizontal or vertical band at the crossings.

Predicted visible tests: first test returns 9 from the single anomaly in a 7-majority row; second returns 2 from either of the two full color-2 rows.

I had already studied this task while repairing its generator, so this is an exposed post-repair solve, not a blind inference record. I did not consult the Racket/reference source during this solve phase.
