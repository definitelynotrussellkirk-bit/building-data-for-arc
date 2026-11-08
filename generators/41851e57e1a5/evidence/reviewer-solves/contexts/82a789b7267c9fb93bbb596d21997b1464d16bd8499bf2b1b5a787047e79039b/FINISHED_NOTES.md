# Post-repair visible-example solve

Earlier rule exposure: **yes**. I authored and reviewed this task's generator
before this episode. This is an exposed post-repair solve, not a blind solve.
During the episode I used the public `solve/README.md` presentation and my own
Python implementation. I did not reopen generator code, Racket/reference
solutions, prior solution explanations, or private labels while solving.

## First hypothesis and actual visible support

The output is a blank same-size canvas containing a solid rectangle colored
by the isolated non-blue/non-red cell. Compute each shape's inclusive
bounding box; the rectangle is their common row and column span.

- Example 0: input 14x15, output 14x15. Red spans rows 2..5 and columns
  10..13; blue spans rows 3..6 and columns 9..12. The common 3x3 area at
  rows 3..5, columns 10..12 matches the displayed nine color-4 output cells.
- Example 1: input/output 14x14. The common span is rows 4..6, columns
  3..6, matching twelve color-5 cells.
- Example 2: input/output 9x9. The common span is rows 2..3, columns 5..6,
  matching four color-6 cells. These cells are blank in the input, so merely
  recoloring existing shape cells cannot explain this example.

The examples use different key colors and change rectangle dimensions, so
neither a fixed output color nor a fixed rectangle size explains all three.
I implemented this direct hypothesis once and submitted it as `intent=solve`.
No deliberate negative or diagnostic attempt was invented. Query inputs are
16x13 and 12x13; their reference outputs and correctness remain unknown to me.

## Check and stopping policy

Run the native visible-only checker. If all three visible examples match and
both query executions succeed, finish this one-attempt episode and retain the
withheld correctness state. The prior exposure declaration remains yes even
if every visible example passes.

## Observed feedback

Revision 1 completed with **3/3 visible examples passed**. The attempt's
reported masked-query label is `unknown`; no query-correctness claim is made.
The first implementation is unchanged. I am finishing because it explains
all available demonstrations and the native check completed successfully.
