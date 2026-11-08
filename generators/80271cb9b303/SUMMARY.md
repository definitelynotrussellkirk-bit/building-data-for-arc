# 80271cb9b303 — extend left-anchored row periods

A zero-background grid contains two to four active rows. Each active row is a
visible prefix of one shared horizontal period, anchored at column zero. Infer
the smallest period consistent through the row's rightmost non-zero cell and
tile it to the right edge; empty rows remain empty.

Current generator version: `3.1.0`. The default three-example curriculum uses
period `4`, then `3`, then a sampled long period in `5..6`; explicit `period`
overrides retain the full `3..6` range. The seven plausible wrong solvers remain
`LESSON_COMPETITORS`, but none fits all four canonical pairs, so
`CANONICAL_SHORTCUTS` is intentionally empty. This distinction is enforced by
`tests/test_semantic_declarations.py`.

The canonical normalized Racket rule hash remains `4cb32d01d908`; neither the
rule nor the generated distribution changed in the semantic-declaration repair.
`workspace/curriculum_probe.py` remains the reusable sequence-level curriculum
probe. Approval is derived by maintainer verification, not by this summary.
