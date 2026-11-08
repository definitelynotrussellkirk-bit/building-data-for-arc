# Visible-only solve work log

This is a human reasoning log for the exposed post-repair episode. I had already
reviewed the assigned generator before this phase, so this is **not blind**. During
this solve phase I used only the visible examples printed by `solve prepare`; I did
not reopen generator code, Racket authority, private labels, reference solutions,
or earlier solution explanations.

## Initial observations

- The modal color is unchanged background: 0 in example 0, 7 in example 1,
  and 5 in example 2.
- Non-background cells form 4-connected components, grouped separately by color.
- A color appearing as only one component is left untouched: color 3 in example 0
  and color 2 in example 2.
- A color split into multiple components is reduced to one selected component.
  The selected component is the largest. Example 1 has two size-6 components of
  color 8; the lower/right one is retained, revealing a positional tie-break.
- The retained component is not merely copied: its bounding box is filled, and
  the filled rectangle extends one column to the left. All other components of
  that color disappear.

## Working rule

For each non-background color independently:

1. Find all 4-connected components.
2. If there is one component, leave that color unchanged.
3. Otherwise choose maximum component size; break a tie in favor of the component
   whose top-left corner is farther down/right. The examples support maximizing
   `top_row + left_column`; exact behavior for an equal-sum residual tie is not
   observable, so the implementation uses row then column as deterministic
   fallback.
4. Erase every cell of that color.
5. Fill the winner's bounding rectangle plus one adjacent column on its left.

## Rejected alternatives

- Keep the first or top-left component: contradicted by color 8 in example 1.
- Keep every maximum-size component: contradicted by the same example, which keeps
  only the lower/right tied component.
- Fill only the ordinary bounding box: contradicted by every transformed color;
  outputs visibly add the column immediately left of the box.
- Apply the operation to a single component too: contradicted by color 3 in
  example 0 and color 2 in example 2, whose irregular shapes remain unchanged.
- Use diagonal connectivity: the visible shapes and retained component counts are
  consistently explained by orthogonal connectivity; diagonal merging would blur
  deliberately separated pieces.

## Implementation notes

The implementation determines background by global frequency, extracts components
from the unchanged input, and applies each color's operation to a copied grid.
Generated examples keep transformed regions separated; overlap ordering is therefore
not inferred from the visible evidence.
