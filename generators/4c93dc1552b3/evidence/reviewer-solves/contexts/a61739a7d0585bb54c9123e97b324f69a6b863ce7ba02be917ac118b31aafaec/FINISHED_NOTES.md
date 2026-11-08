# Solve notes

The visible examples show that only blue (1) objects change. I treated blue cells as four-connected components rather than scanning arbitrary bounding boxes, because the irregular blue examples remain unchanged even when their bounding boxes are at least 2×2.

Hypothesis: a blue component qualifies exactly when it completely fills its bounding box and both dimensions are at least two. For each qualifying component, change its four bounding-box corners to red (2); preserve every non-corner blue cell and every non-blue object. This explains the 2×2 cases (all four cells become red), larger solid rectangles, edge-touching rectangles, and the unchanged irregular components.

Implementation: flood-fill each blue component, compare component size to bounding-box area, then recolor the four corners in a copied grid. I had already inspected the generator and rule before this required exposed solve, so this is not a blind inference record; I did not consult a reference during the solve phase.
