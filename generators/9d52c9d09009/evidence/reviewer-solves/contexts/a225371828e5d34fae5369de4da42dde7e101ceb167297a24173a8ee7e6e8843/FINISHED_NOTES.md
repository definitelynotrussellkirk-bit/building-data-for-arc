# Solve work log

## Exposure declaration

Before this masked solve episode was prepared, I had already inspected the task's generator and canonical-rule evidence while repairing the package. I therefore declare earlier exposure. After `solve prepare`, I kept those sources closed and derived/implemented this solver from `challenge.json` alone; I did not consult a reference implementation or private query labels during the solve.

## Visible-example observations

Each input contains several separated, 4-connected objects made of color 8. The output keeps every zero in place and recolors all cells of a given 8-object uniformly. The replacement varies object by object, so it is a property of the object's internal pattern rather than its size, position, or the whole canvas.

For each object I considered its tight bounding rectangle and counted the distinct 4-connected zero regions inside that rectangle. This reproduces the displayed colors 1, 2, and 3. Objects with four such zero regions are displayed as color 7 rather than color 4; the repeated train shapes make this exceptional mapping visible. Thus the inferred mapping is `count`, except `4 -> 7`.

## Implemented hypothesis

1. Find each 4-connected component of color 8.
2. Compute that component's tight bounding box.
3. Count 4-connected components of zero cells restricted to that box.
4. Recolor only the component's 8-cells with that count, using color 7 for count four.
5. Preserve all other cells.

I used 4-connectivity both for separating objects and for the zero-region count. Diagonal zero contact therefore does not merge regions. Remaining uncertainty is limited to unseen counts outside the demonstrated range; I retain the literal count for those rather than invent another special code.
