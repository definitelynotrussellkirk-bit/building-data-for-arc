# Post-repair visible-only solve notes

I had already inspected this task's generator and canonical rule during the repair,
so this is **not blind**. During this separate solve I used only the presentation
created by `review.py solve prepare`; I did not reopen the generator, Racket rule,
private labels, or earlier solution explanations.

## Hypothesis

Each input is two aligned three-column panels separated by a uniform one-column
bar. The output keeps the common height and three-column width. For each output
position `(r, c)`, compare input `(r, c)` in the left panel with `(r, c + 4)` in
the right panel:

- output `2` when at least one aligned input cell is nonzero;
- output `0` only when both aligned cells are zero.

The panel colors and separator color do not transfer to the output; they mark
roles. This is an occupancy union.

## Visible checks

- Train 0 row 0 has relations `00, 10, 11`, yielding `0, 2, 2`.
- Train 1 row 1 has `00, 10, 11`, yielding `0, 2, 2`.
- Train 2 includes different height and colors yet follows the same cellwise
  overlay, ruling out fixed color or fixed-size copying.

The implementation applies this directly and validates the visible `h x 7`
shape. No diagnostic or intentionally wrong attempt was needed.
