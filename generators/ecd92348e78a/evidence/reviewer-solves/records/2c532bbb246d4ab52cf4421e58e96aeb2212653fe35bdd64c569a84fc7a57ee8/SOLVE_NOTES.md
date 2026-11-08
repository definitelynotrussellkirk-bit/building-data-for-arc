# Solve work log

## Exposure

This is the required post-repair solve, so I had already seen the assigned
family's generator behavior before `solve prepare`. After preparation I kept the
generator, Racket rule, reference solutions, private query labels, and earlier
solution explanations closed. I used only the visible grids in
`solve/challenge.json` and local experiments against those visible examples.

## Visible hypothesis

Each nonzero color becomes one output column. The height of that column is the
vertical extent of the color in the input: `max_row - min_row + 1`, not its cell
count and not its horizontal width. Columns are ordered by decreasing measured
height and filled from the top; unused cells below a shorter column are zero.

The examples distinguish the main alternatives:

- Train 0: color 7 has 15 cells but bbox height 5, while color 5 has only 6 cells
  and bbox height 6; the output puts color 5 first, refuting sorting by cell count.
- Train 1: color 4 spans one row despite two cells, so its output bar has height 1.
- Train 2: the ordered heights are 5, 4, 3, 1 and all shorter bars are top-aligned.

For an unshown tie I use ascending color order as a deterministic convention; the
visible examples do not establish a different tie policy.

## Test-first implementation

1. Added `checks/post-solve-tdd/test_visible.py` before changing the solution.
2. Confirmed the initial skeleton failed with `NotImplementedError`; the failure
   is retained in `checks/post-solve-tdd/red.stderr`.
3. Implemented per-color row bounds, descending height order, and top-aligned bar
   rendering.
4. Re-ran the visible-example harness before recording an official attempt.
