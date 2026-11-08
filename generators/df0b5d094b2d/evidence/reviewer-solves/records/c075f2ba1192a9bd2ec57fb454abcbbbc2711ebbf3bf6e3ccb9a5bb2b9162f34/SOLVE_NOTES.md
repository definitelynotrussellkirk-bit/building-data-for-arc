# Solve work log

## Exposure and constraints

I had not opened this task's generator, canonical rule, reference solution, private labels, audit evidence, or any generator source before preparing this blind episode. I used only the visible grids printed by `review.py blind prepare` and the copied challenge presentation.

## Hypothesis

Every non-background object is a solid rectangle except that one corner cell is colored 8. The 8 marks both the missing rectangle cell and a diagonal direction. The output replaces the 8 with the object's color, erases the old object, and translates the completed rectangle one row and one column toward the marked corner:

- top-left marker: up and left;
- top-right marker: up and right;
- bottom-left marker: down and left;
- bottom-right marker: down and right.

This explains all visible examples, including multiple objects and neighboring objects of different colors. The background is the most frequent color (7 in every visible grid).

## Implementation and probes

The solver locates each 8 marker, associates it with an adjacent 4-connected colored component, verifies that the component plus marker exactly fills a rectangular bounding box with the marker at a corner, then draws the completed rectangle shifted one diagonal step. Associating each marker with a component rather than globally grouping by color also handles more than one rectangle of the same color.

I tested the implementation locally against all three visible training pairs before submitting the revision. Remaining uncertainty is limited to unseen malformed inputs (for example, a marker not belonging to a filled rectangle); the visible task strongly supports the rectangle contract.
