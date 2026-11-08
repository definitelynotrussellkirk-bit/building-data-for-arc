# Solve notes

Earlier exposure: yes. I repaired this task before the post-repair solve, so this is not blind. During this solve I did not reopen the generator, Racket rule, reference labels, or prior solution explanations.

From the visible examples:

- Each nonzero color forms one 4-connected object.
- The output contains each object's tight crop, retaining internal zero cells.
- Crops are top-aligned and separated by one zero column.
- The ordering is not source position, color, or area. Computing exposed 4-neighbor edge counts gives the visible order.
- Equal-perimeter objects retain source row-major bbox order: top row, then left column.

Implemented: extract same-color 4-connected components, compute true exposed-edge perimeter, sort by `(perimeter, bbox_top, bbox_left)`, and horizontally pack tight crops with one zero column.
