# Visible-only solve notes

This is a human-readable work log written after `solve_episode.py prepare`. I had already inspected the assigned generator and canonical rule during the repair phase, so this episode is **not blind**. During this solve phase I used only the prepared visible examples and did not reopen the generator, Racket rule, canonical ledger, reference solutions, private labels, or earlier solution explanations.

## Hypothesis

Each nonzero color forms a separate object. Within that object's own bounding box, find every 4-connected zero region that does **not** touch the bounding-box boundary. Those are the object's enclosed holes. Union all enclosed regions, crop the union to its tight bounding box, and recolor its cells with the object's color.

Sort the resulting cropped patterns by the original object's leftmost column. Pack them horizontally, top-aligned, with one all-zero separator column.

The missing corners in train examples 0, 2, and 3 are useful negative evidence: a zero on an object's bounding-box boundary is exterior background and must not be copied. Train examples 0/2 show a nonrectangular enclosed pattern; examples 1/3 show multiple enclosed regions separated by colored material.

## Predicted queries

- Query 0: both 3×3 rings have one-cell holes, so the output should be `[[4, 0, 6]]`.
- Query 1: the color-3 hole is a 3×3 mask with only its middle-left cell absent; the color-2 hole is a 1×3 bar. Packed result:

```text
3 3 3 0 2 2 2
0 3 3 0 0 0 0
3 3 3 0 0 0 0
```

## Implementation

The solver independently implements same-color 4-connected components, bounded-box zero-region flood fill, tight normalization, left-to-right sorting, and top-aligned horizontal packing. It does not depend on task or generator modules.
