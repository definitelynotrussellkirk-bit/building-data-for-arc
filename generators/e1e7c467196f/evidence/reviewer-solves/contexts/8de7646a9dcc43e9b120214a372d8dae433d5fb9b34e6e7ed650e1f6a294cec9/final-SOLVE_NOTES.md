# Solve notes

This is a human work log for the prepared visible-example episode. I had earlier exposure to the task rule while reviewing the generator, so this is not claimed as a blind solve. During this solve phase I read only `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solution, private labels, or prior solution explanations.

## Revision 1 — positional one-way legend substitution

Hypothesis from the three visible training examples:

1. The first two rows form a positional legend: each nonzero color in row 0 maps to the color directly below it in row 1.
2. Both legend rows are cleared to zeros in the output.
3. In rows 2 onward, replace only row-0 source colors using that mapping.
4. Preserve zeros, row-1 target colors already present in the body, and unrelated colors.

Visible checks supporting the one-way direction:

- Training example 2 contains body color `3`, which is a target color, and it remains `3`; body source colors `4` and `7` become `5` and `3`.
- Training example 3 contains body color `8`, also a target color, and it remains `8`; unrelated body color `2` remains `2`.
- All examples erase exactly the first two rows and preserve body geometry.

Implementation: construct a dictionary from aligned nonzero entries of the first two rows, zero the first two rows, and apply `mapping.get(value, value)` to the remaining cells. No failed revision was manufactured because this hypothesis accounts for every visible changed and unchanged cell.
