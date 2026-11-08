# Solve work log

## Exposure declaration

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private query labels, prior solution explanations, or the selected
repair generator. I used only the visible examples printed by `blind prepare`.

## Revision 1 — orthogonal red/green pair consumption

Across all three training examples, a red cell (`2`) disappears exactly when it
shares an edge with a green cell (`3`). The adjacent green cell changes to azure
(`8`). Unmatched reds and greens remain unchanged, as do gray markers (`5`).
The examples contain all four relative directions: green left/right/above/below
red. Diagonal proximity is not supported as a match.

The implementation scans the original grid, not the partially transformed
output, so simultaneous contacts are handled consistently: every matched red is
erased and every matched green is recolored even when one cell has multiple
neighbors. A local visible-example regression script was run first against the
untouched template and failed with `NotImplementedError`, then passed after this
implementation.

Alternative considered: treat only isolated dominoes or pair cells greedily.
The training examples do not require a one-to-one matching, and a local adjacency
rule is simpler and better supported. Remaining uncertainty is limited to unseen
multi-neighbor clusters; simultaneous original-grid adjacency is the least
arbitrary extension.
