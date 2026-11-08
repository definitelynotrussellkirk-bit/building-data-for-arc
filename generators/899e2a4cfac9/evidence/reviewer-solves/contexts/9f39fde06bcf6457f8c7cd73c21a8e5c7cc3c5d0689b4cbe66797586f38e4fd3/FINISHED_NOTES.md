# Visible-example solve: one implementation revision

## Exposure and scope

Earlier exposure: **yes**. I repaired this task's generator before this episode, so this is not an independent blind solve. During this episode I read only this directory's README, challenge, initial solution template, and my own solution/work log. I did not consult generator source, the Racket rule, reference solutions, private labels, or earlier solution notes while solving. The earlier task exposure remains a limitation even though no reference was consulted during the episode.

## Observations from the visible training pairs

All three outputs retain their input dimensions and use zero to erase colored cells. In examples 0 and 2, the two objects that reach an outside edge disappear, while the wholly interior object keeps its cells and color. Example 1 separates the important alternatives: an interior one-cell color-4 object survives; an interior color-4 domino survives despite a different color-4 object touching the right or bottom edge; and the interior color-3 object survives despite diagonal contact with a different color-3 object that reaches the left edge. The color-4 domino immediately below color 7 survives, so touching objects of different colors must remain separate. These examples support same-color, four-neighbor components and deletion of the entire component if any of its cells reaches an edge.

## Revision 1

Implement a flood fill for each nonzero same-color component, using only up, down, left, and right neighbors. Mark a component if any cell lies on the first/last row or column, then replace every cell of that component with zero. Preserve all other cells. This also preserves singleton and small interior components; object size and a color's presence elsewhere do not determine deletion.

The supported solve check completed with **3/3 visible examples passed** and no execution error. No deliberately incorrect preliminary revision was created. I stopped after this one implementation revision because the visible examples gave no evidence for another change. Masked query outputs have not been inspected and their correctness is unknown to me.
