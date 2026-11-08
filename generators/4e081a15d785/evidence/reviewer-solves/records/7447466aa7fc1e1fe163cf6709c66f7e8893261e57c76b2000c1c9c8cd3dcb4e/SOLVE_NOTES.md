# Blind solve work log

## Scope and exposure

I read only `WORK/solve-blind/README.md` and `WORK/solve-blind/challenge.json` to establish the puzzle. I have not read a generator, rule implementation, canonical data, reference solution, private labels, earlier solution, or audit evidence. I have no earlier exposure to this puzzle's rule.

The visible data contain three labeled training examples and two unlabeled test inputs. The training shapes are 7x7 -> 4x4, 8x10 -> 5x6, and 3x3 -> 1x3. Test input shapes are 4x7 and 5x8.

## Initial hypothesis, before running a check

Collapse every consecutive run of identical whole rows to one row. Likewise collapse consecutive runs of identical whole columns to one column. Preserve order and retain repeated patterns when they are separated by a different pattern. Equality is of complete rows or columns, rather than individual runs of colors within a row.

Visible evidence:

- Training example 0 has row-pattern runs of lengths 1, 2, 3, 1, giving four retained rows. Its column-pattern runs have lengths 1, 1, 2, 3, giving four retained columns. The repeated top-row pattern later in the input remains because another row pattern separates the runs.
- Training example 1 has row-pattern runs of lengths 2, 2, 2, 1, 1 and column-pattern runs of lengths 3, 1, 2, 2, 1, 1, giving the observed 5x6 shape and matching the shown cell patterns.
- Training example 2 consists of three equal rows with three distinct columns, giving the shown 1x3 output.

The implementation in `solution.py` first keeps one row per adjacent equal-row run, then compares complete column tuples and keeps one column per adjacent equal-column run. Removing duplicate rows cannot erase a distinction between two columns, because one representative of every removed equal row remains. The function returns new lists and does not modify the input.

Predictions from this hypothesis, not private correctness claims:

- Test query 0: 2x4, `[[4, 0, 6, 4], [0, 4, 0, 0]]`.
- Test query 1: 3x4, `[[7, 7, 5, 7], [7, 5, 5, 7], [7, 7, 5, 7]]`.

This is the first implementation. No earlier revisions or failed checks have occurred. The next action is the authorized blind check, which provides visible-example and execution feedback while withholding private query correctness.
