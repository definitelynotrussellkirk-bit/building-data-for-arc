# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, reference answers, prior solution explanations, or audit evidence for task `595eebab5aea`. I used only the public examples printed by `review.py blind prepare`, `challenge.json`, and local visible-example checks.

## Revision 1 — deliberate red baseline

The prepared `solution.py` stub raised `NotImplementedError`. I ran the checker before implementing anything so that the first recorded revision was an honest failing baseline. It produced an execution error and passed 0/5 visible examples.

## Inferred transformation

The first row contains three isolated color markers. The remainder contains three monochrome connected shapes. The output:

1. sorts the shapes by descending cell count;
2. breaks equal-size ties by the source shape's leftmost column;
3. assigns the marker colors in left-to-right marker order to those sorted shapes;
4. crops each shape to its bounding box, recolors it, and horizontally centers it in a canvas whose width is the widest cropped shape; and
5. stacks the shapes vertically with one all-zero row between consecutive shapes.

The centering detail explains the otherwise surprising leading zero in narrow shapes: with a four-column output, width-1 and width-2 shapes begin at column 1, while width-3 and width-4 shapes begin at column 0. This matched all five demonstrations. The equal-size examples show the left-to-right tie break.

## Implementation notes and remaining uncertainty

The program finds 4-connected nonzero components below row 0, preserves each component's exact mask inside its bounding box, and validates that the marker/object counts match. The two query predictions are therefore generated from the same structural rule rather than hard-coded grids. The principal uncertainty is whether an unseen task variant could use disconnected pieces of one color as one logical object; the visible examples consistently use one connected component per object, so I retained the simplest supported interpretation.
