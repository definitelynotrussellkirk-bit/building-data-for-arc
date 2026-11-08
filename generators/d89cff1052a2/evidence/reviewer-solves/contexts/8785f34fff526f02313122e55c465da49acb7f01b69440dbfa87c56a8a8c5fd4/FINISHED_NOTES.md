# Post-repair visible-only solve: d89cff1052a2

## Exposure boundary

Earlier rule exposure: **yes**. I reviewed and repaired this generator before
this solve, so this is an exposed post-repair exercise, not a blind inference.
After `review.py solve prepare`, I used only its displayed visible examples
and query inputs. I did not reopen generator code, any Racket rule, private
labels, previous solve explanations, or canonical helpers during this solve.

## Visible observations and hypothesis

The training shapes are 3x4 -> 6x4, 6x4 -> 12x4, and 3x4 -> 6x4.
Each output's bottom half is the original grid, and its top half has input
rows in reverse order. Within each row, left-to-right order is preserved.
The two halves meet at duplicated copies of the original first row.

Hypothesis: prepend the complete vertical reflection to a copy of the input.
The 6-row demonstration rules out mirroring exactly three rows. Its first
and last rows differ, so duplication without reflection is also contradicted.
The asymmetric horizontal patterns rule out reversing columns instead of rows.

## Revision 1

Implemented arbitrary-height row reversal followed by the original row order.
Returned rows are fresh lists, so the solver does not mutate its input.
Query inputs are 5x5 and 3x4; their reference outputs and their dimensions
remain hidden. There is no genuine failed hypothesis in this solve, and no
deliberately wrong attempt has been introduced.

Stopping rule: stop when the official visible-example/execution check passes;
leave masked-query correctness to independent maintainer scoring.
