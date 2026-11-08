# Solve work log

## Exposure

I had not opened the task's generator, canonical rule, reference solutions,
private labels, audit records, or earlier solution explanations.  I used only
the visible examples printed by `review.py blind prepare` and repeated in the
public README.

## Revision 1 — diagonal shadow hypothesis

Across training example 1, every maroon (`9`) cell has exactly one new gray
(`5`) cell at offset `(row + 1, column - 1)`.  The same offset explains the
other examples with two clipping rules:

- in example 0, one destination is occupied by a blue cell and another falls
  below the grid, leaving only the one legal gray cell;
- in example 2, the destination below-left of `(5, 6)` is occupied by blue at
  `(6, 5)`, while all four other legal background destinations become gray.

I therefore implemented: copy the grid, inspect the original maroon cells, and
paint gray one step down-left only when the destination is in bounds and still
background.  Existing colored cells are preserved.  The blue/yellow objects
appear to act as blockers rather than selecting a different direction; the
training examples provide no evidence for changing the offset by their shape or
color.

Remaining uncertainty: a different hidden rule could assign semantic meaning to
the non-maroon object, but the fixed offset plus collision/boundary behavior is
the simplest rule explaining every changed and unchanged cell.
