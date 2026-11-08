# Solve work log

## Exposure declaration

Before this solve I had read only the packet-level instructions and assignment duties. I did **not** inspect this task's generator, Racket rule, canonical record, reference solution, private query labels, prior notes, or audit evidence.

## Revision 1 — horizontal one-cell-gap completion

Across all three visible examples, every changed cell is a zero horizontally bracketed by two equal nonzero cells:

- `7 0 7 0 7 0 7` becomes a solid run of `7`.
- `1 0 1` becomes `1 1 1`.
- Rows containing same-colored points three columns apart, diagonal relationships, vertical pairs, or isolated points remain unchanged.

Hypothesis: independently replace each zero cell whose immediate left and right neighbors are the same nonzero color. Evaluate the predicate against the original input and write into a copied grid, so the transformation does not cascade from newly created cells.

This predicts query 0 will fill the three gaps in the row of four `7`s and the single gap between the two `4`s. Query 1 will fill the three gaps in the row of four `6`s; all other cells remain unchanged.

Remaining uncertainty: unseen inputs could phrase the rule as completing maximal alternating horizontal sequences, but on the visible domain that is equivalent to the local bracket predicate and the local form avoids extending across larger or obstructed gaps.
