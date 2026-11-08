# Solve notes

This is a human-readable work log based only on the prepared visible episode.
I had earlier rule exposure during generator review, so this is not a blind solve;
I did not reopen the generator, Racket rule, reference solution, or private labels
while solving this episode.

## Hypothesis

The 3×3 input is simultaneously a 3×3 block-selection mask and the template
copied into selected blocks. The 9×9 output is partitioned into nine 3×3
blocks. At input position `(r, c)`, a nonzero cell places an exact copy of the
whole input into output block `(r, c)`; a zero cell leaves that block all zero.

Checks against the visible examples:

- Example 0 has three nonzero mask cells and therefore three copies, for
  `3 × 3 = 9` nonzero output cells.
- Example 1 has six nonzero mask cells and six nonzero cells in the template,
  giving `6 × 6 = 36` nonzero output cells.
- Example 2 similarly gives `7 × 7 = 49` nonzero output cells.
- The visible block layouts and within-block patterns match the input exactly,
  ruling out simple 3× pixel scaling and repetition into every block.

The implementation is dimension-generic, although the visible task uses 3×3
inputs.
