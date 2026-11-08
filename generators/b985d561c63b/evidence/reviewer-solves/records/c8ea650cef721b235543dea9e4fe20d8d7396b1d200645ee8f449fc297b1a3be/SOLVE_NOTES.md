# Solve work log

I had not seen the rule, generator, private labels, prior solution notes, or any task-specific source before this blind solve. I used only the prepared visible examples.

## Revision 1 — failed

Initial hypothesis: copy the full gray-block-sized source canvas, including background. The checker reported 2/3 visible examples passed. Train example 1 is the counterexample: this erased gray beyond the sparse motif's tight extent.

## Revision 2

Revised hypothesis: overlay only non-background colored stencil cells at their relative offsets within each gray rectangle, leaving all uncovered gray unchanged.

This should avoid over-erasing in train example 1. Remaining question: whether a background hole *inside* the stencil's tight bounding box should clear gray.
