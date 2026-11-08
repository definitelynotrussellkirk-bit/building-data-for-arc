# Solve work log

## Prior exposure

Before this visible-only episode I had already reviewed the selected generator and its authority, so this is not a blind solve. During this episode I did not reopen the generator, Racket rule, reference solutions, or private labels.

## Revision 1 — smallest green connected component

Visible evidence: each training input contains several 4-connected color-3 components plus inert color-5 marker cells. In every output, exactly one entire color-3 component changes to color 4; the changed component has the fewest cells (sizes 2 of 2/3/4, then 1 of 1/3/4, then 2 of 2/3/5). Component position varies, while color-5 cells and all larger green components remain unchanged.

Hypothesis: enumerate orthogonally connected color-3 components, require a unique minimum by cell count, and recolor all cells of that component to 4. Preserve every other cell. Diagonal contact is not treated as connectivity.

Implementation: iterative flood fill and a copied output grid. The no-component or tied-minimum fallback returns the unchanged grid; neither fallback is needed by the visible examples, but it avoids arbitrary edits outside the observed rule.

Alternatives rejected from visible evidence: recolor the first/last component, recolor a fixed size, or select by position. The winning component appears first, middle, and last across the three examples, and its size changes from 2 to 1 to 2.
