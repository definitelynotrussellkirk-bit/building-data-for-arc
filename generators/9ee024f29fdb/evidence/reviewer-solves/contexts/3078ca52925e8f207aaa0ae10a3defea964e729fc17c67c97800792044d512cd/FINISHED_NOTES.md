# Solve work log

## Exposure declaration

I had already inspected this task's generator and canonical rule while repairing it, so this is an exposed post-repair solve. During this solve phase I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, or private query labels.

## Revision 1

Hypothesis from the three visible examples: zero-based rows and columns 0, 4, 8, 12, ... form a fixed lattice and are always cleared. At every other coordinate, cyan 8 is erased to 0 while every other input color—including background 0 and the visible decoy colors 1 and 4—is painted red 2.

Visible probes supporting the fixed-coordinate interpretation:

- Train 1 contains nonzero values on periodic lines (for example row 0 and column 0/12); all are still cleared, so the lattice is not detected merely as all-zero input lines.
- Interior 1 and 4 cells become 2, so the operation is not a binary 0/8 inversion that preserves unfamiliar colors.
- Train 0 and Train 2 show the same four-cell period across different 5×9 and 13×9 shapes.

Implementation applies the cellwise rule without mutating the input. Remaining uncertainty before checking: none material; the visible examples directly exercise noisy lattice lines and decoy colors.
