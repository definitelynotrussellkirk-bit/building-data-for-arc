# Exposed post-repair solve notes — 7fc158ab7b70

This is a human work log based on `solve/challenge.json`. I had already inspected
the generator while reviewing it, so this solve is explicitly **exposed**. After
preparation I did not reopen the generator, Racket rule, reference solution,
private labels, or any earlier solution explanation.

## Visible-example inference

- Example 1 has a 3×3 input with four nonzero cells and a 12×12 output. Each
  source cell becomes a uniform 4×4 block.
- Example 2 has a 4×4 input with five nonzero cells and a 20×20 output. Each
  source cell becomes a uniform 5×5 block. Repeated colors still count as
  separate occupied cells.
- Example 3 has a 5×5 input with four nonzero cells and a 20×20 output. Each
  source cell becomes a uniform 4×4 block.

The common rule is nearest-neighbor upscaling by the number of nonzero cells.
The two test inputs each contain four nonzero cells, so each source cell should
expand to a 4×4 block.

## Revision 1

Implemented the direct block expansion with scale equal to the occupied-cell
count. No deliberate negative or diagnostic revision was needed.
