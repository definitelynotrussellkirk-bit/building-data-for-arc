# Solve work log

I had not opened either this task's generator/rule/notes or the assigned repair generator before this solve. I used only the visible examples printed by `blind prepare` and the generated `README.md`.

## Revision 1 — repeated shape repairs the outlier

Across the examples, the input contains several separated objects. Two or more objects share exactly the same normalized binary shape, while one object has a different shape. The output is the repeated shape, cropped to its bounding box and painted with the colour of the odd-shaped object. When all objects have one colour (train example 1), the same rule naturally preserves that colour.

I implemented same-colour 4-connected component extraction, normalized each component to a binary bounding-box mask, selected the most frequent exact mask, and painted it with the colour of a component whose mask differs. I deliberately did not canonicalize rotations or reflections because the visible examples repeat the desired orientation exactly and the output preserves it.

Expected visible-query predictions:

- Query 0: a 3×2 mask `[[2,0],[2,2],[2,0]]`, because that shape appears twice and the smaller L-shape is the outlier (all colour 2).
- Query 1: a 2×5 mask `[[5,5,0,0,0],[0,5,5,5,5]]`, because the two colour-1 objects share that shape and the colour-5 zigzag is the outlier.

Remaining uncertainty: if a future instance used repeated shapes only up to rotation/reflection, this exact-mask interpretation would not generalize, but the visible training data provides no evidence for such normalization.
