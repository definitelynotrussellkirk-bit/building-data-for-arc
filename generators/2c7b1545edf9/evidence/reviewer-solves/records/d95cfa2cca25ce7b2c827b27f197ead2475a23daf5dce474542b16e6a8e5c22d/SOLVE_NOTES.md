# Solve work log

## Exposure statement

I prepared and examined only the visible challenge presentation and my own scripts. I did not open the task's generator, Racket rule, canonical answers, private labels, earlier solution explanations, or my assigned repair target before this solve.

## Observations and hypotheses

Each input contains several monochrome 4-connected objects on black. Every demonstrated output is an exact crop of one whole object, retaining black cells inside its bounding box.

The selected objects have these visible component statistics:

- Example 0, color 8: 6 cells, perimeter 14, graph diameter 5, bounding box 4x3.
- Example 1, color 7: 7 cells, perimeter 16, graph diameter 5, bounding box 4x4.
- Example 2, color 7: 8 cells, perimeter 18, graph diameter 7, bounding box 4x3.

A simple "largest component" rule explains examples 1 and 2 but is tied in example 0: color 3 also has 6 cells and perimeter 14. The selected color-8 object has graph diameter 5 versus 4 for color 3. I therefore used a color-independent lexicographic ranking: cell count, exposed perimeter, graph diameter, then bounding-box area. This chooses all three demonstrated targets.

The first query also has two 8-cell objects. The color-7 object has perimeter 16 versus 14 for color 3, so the proposed ranking selects color 7. The second query selects the unique 8-cell color-1 object. This is still an inference from finite examples; another hidden tie-break rule may exist.

## Implementation

I enumerate same-color 4-connected components, compute the ranking above, crop the selected component to its bounding box, and preserve zeros in the crop. The solver does not use absolute position or color identity.
