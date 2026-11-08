# Visible-only solve work log

Earlier rule exposure exists because this solve follows the assigned generator repair. During this solve phase I used only the visible examples in `README.md`; I did not reopen the generator, Racket rule, canonical ledger, or reference explanation.

## Hypothesis

The first row is a left-to-right instruction strip. Its nonzero cells are not part of the picture. Rows below it contain the payload, which is first cropped to its nonzero bounding box. Comparing the visible input/output pairs gives the command meanings:

- `1`: reflect left/right.
- `2`: reflect up/down.
- `3`: rotate 90 degrees clockwise.
- `4`: rotate 180 degrees.

Commands are applied sequentially in row order. Colors `1..4` below the first row remain payload; train example 2 makes that distinction visible.

## Implementation

`solution.py` independently crops rows 1+, then applies the four elementary transforms. No task package or reference helper is imported. I expect this to handle both visible queries and arbitrary rectangular crops, including shape-changing quarter turns.
