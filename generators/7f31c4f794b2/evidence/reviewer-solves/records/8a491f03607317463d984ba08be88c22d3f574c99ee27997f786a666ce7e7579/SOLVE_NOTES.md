# Visible-only solve notes

## Observations

Across all three demonstrations, the output keeps the grid size and background unchanged. Whole monochrome objects either remain unchanged or are recolored uniformly to 7.

The deciding property is border contact at the connected-component level:

- In train 1, the top 6-object and top/right 8-object become 7, and the right-edge 9-object becomes 7; interior 6, 1, and 8 objects remain unchanged.
- In train 2, the top 9-object, left 6-object, and right 1-object become 7, while the separate interior 9-object remains 9. This rules out a global rule such as “replace every occurrence of a color seen on the border.”
- In train 3, the top 3-object and left 1-object become 7, while a separate interior 3-object remains 3.

## Hypothesis

Find each nonzero same-color 4-connected component. If any cell of that component lies on the outermost row or column, recolor the entire component to 7. Leave all other cells unchanged.

## Implementation choice

Use an iterative four-neighbor flood fill for each unseen nonzero cell. Record the component and whether it touches any grid edge, then recolor only that component in a copied output grid.

## Alternatives rejected

- Recolor all nonzero cells: contradicted by unchanged interior objects.
- Recolor by color globally once that color appears on an edge: contradicted by train 2 and train 3, where an edge-touching component and an interior component share a color but receive different treatment.
- Consider diagonal connectivity: the examples support ordinary four-neighbor components; diagonal merging would incorrectly couple some separated shapes.
