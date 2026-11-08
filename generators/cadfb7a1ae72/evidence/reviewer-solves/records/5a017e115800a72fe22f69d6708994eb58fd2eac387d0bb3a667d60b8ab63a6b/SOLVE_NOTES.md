# Solve notes

This is a human-readable work log written during the required reviewer solve. I had already seen the task's rule while repairing the generator, so this is **not blind**; I did not consult the generator, Racket source, reference solution, or private labels during this solve phase.

## Visible-example hypothesis

The output is an `N × N` symmetric matrix, where `N` is the number of non-zero same-color connected objects read in top-left order.

From the visible demonstrations:

- The diagonal is always `1`, suggesting identity of object index.
- Off-diagonal `8` pairs share the same reflection behavior. In particular, the fourth demonstration's first and fifth objects are both asymmetric in the same row/column-reflection sense, despite having different sizes.
- Off-diagonal `4` pairs do not share the same exact symmetry class but do share the number of enclosed background regions inside their bounding boxes.
- Remaining pairs are `0`.
- Row-only and column-only reflection must be treated as different classes, not merely “one symmetry axis.”
- The visible examples also support precedence: exact symmetry is tested before equal hole count.

## Planned probe and implementation

1. Extract each non-zero 4-connected component using same-color adjacency.
2. Normalize each component to its bounding box and sort components by `(top row, left column)`.
3. Count enclosed zero regions in the normalized bounding box using 4-connectivity.
4. Record horizontal-axis (row reflection) and vertical-axis (column reflection) symmetry as two separate bits.
5. Emit `1` on the diagonal, otherwise `8` for equal symmetry bits, `4` for equal hole count, and `0` otherwise.

The implementation is pure Python and does not mutate the input.
