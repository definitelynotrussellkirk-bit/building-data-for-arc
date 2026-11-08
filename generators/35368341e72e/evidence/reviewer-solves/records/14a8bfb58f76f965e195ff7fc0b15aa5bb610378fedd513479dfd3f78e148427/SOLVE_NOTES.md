# Visible-only solve notes

The top row contains nonzero labels.  Each label sits above the center of a
three-column block in rows 1--3, so those rows encode a 3x3 prototype for the
label.  The all-zero penultimate row separates this dictionary from the final
query row.

For every nonzero label in the final row, in left-to-right order, the output
copies that label's 3x3 prototype.  Consecutive copies are separated by one
all-zero column.  Repeated query labels therefore repeat the same prototype;
they are not deduplicated.

I implemented exactly that lookup-and-concatenate rule in `solution.py`.  The
three visible training examples should produce widths 11 = 3 + 1 + 3 + 1 + 3,
including examples where a label is queried more than once.

Earlier in the repair assignment I had seen the task's rule-related source.
For this required post-repair solve, I kept generator, Racket rule, reference
answers, private labels, and prior solve notes closed after `prepare`; the
reasoning above uses only the visible examples reproduced in `solve/README.md`.
