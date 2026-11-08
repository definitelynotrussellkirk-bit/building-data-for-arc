# Solve work log

## Exposure declaration before solving

I had already read the selected generator and canonical Racket rule during the repair phase, so this is not a blind solve. During this solve phase I used only the displayed visible examples/challenge and did not reopen the generator, Racket source, reference solution, private query labels, or earlier solve explanations.

## Revision 1

The four visible examples each contain four differently colored 8-connected objects on cyan (8). In every output, the cell of each smaller object closest to the grid center disappears. The largest object keeps that inward-pointing cell and gains a three-cell bar immediately outside its far edge, centered on the retained tip's row or column. This interpretation explains the constant color-count changes: each of three smaller colors loses one cell, while the target color gains three.

I implemented 8-connected component extraction, selected the unique largest component, found each object's center-facing tip by minimum squared distance to the grid center, erased the three non-target tips, and inferred the target's pointing axis from its tip relative to its bounding-box center. The added bar goes outside the opposite bounding-box edge. I used no query answer or reference execution.

Remaining uncertainty before checking: a tie in nearest-center cells would need a rule, but every visible object appears designed with a unique tip; likewise the largest object is visibly unique.
