# Exposed post-repair solve notes

This is a human work log based only on `solve/challenge.json`. I had already seen the task rule during the generator review, so this episode is explicitly exposed rather than blind; I did not reopen the generator, Racket source, reference solution, or private query labels while solving.

## Visible-example inference

- Lesson 1 is 3×3 with five nonzero cells and a 15×15 output. Every source cell becomes a uniform 5×5 block.
- Lesson 2 is 4×4 with three nonzero cells and a 12×12 output. Every source cell becomes a 3×3 block, including both occurrences of color 6.
- Lesson 3 is 5×5 with four nonzero cells and a 20×20 output. Every source cell becomes a 4×4 block.

The common rule is therefore nearest-neighbor expansion with scale equal to the **number of nonzero cells**, not the number of distinct nonzero colors. The second lesson is the decisive visible witness: it has three occupied cells but only two distinct colors, and its scale is three.

## Revision 1

Implemented a direct row/column block expansion. It computes the nonzero-cell count, repeats every cell horizontally by that count, then repeats each expanded row vertically by the same count. I expect all three visible lessons to match exactly and both queries to use the same rule.
