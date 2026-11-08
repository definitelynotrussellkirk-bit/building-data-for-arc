# Solve notes

## Revision 1

Visible examples suggest treating each same-colour 4-connected foreground object independently. The output starts from a black grid and draws the hollow perimeter of each object's tight axis-aligned bounding rectangle in that object's colour. This explains both additions (missing rectangle-border cells appear) and deletions (source cells strictly inside the rectangle disappear), while preserving independent objects even when different colours touch.

Implementation probe: flood-fill same-colour 4-neighbour components, compute each component's min/max row and column, and paint only cells on those four bounds into a fresh zero grid. The output dimensions remain equal to the input dimensions in all visible examples.
