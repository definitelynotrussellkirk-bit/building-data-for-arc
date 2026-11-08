# Post-repair visible solve notes

## Revision 1

The examples preserve canvas size and erase no foreground cell, but add color only inside tight axis-aligned rectangles around foreground groups.

- Train 0: the lower-left and lower-right color-8 groups become separate 2x3 rectangles, while color 3 becomes its own 3x2 rectangle.
- Train 1: each color is filled independently to its tight rectangle.
- Train 2 is the decisive segmentation probe: color 9 occurs in two disconnected groups. The output fills two local 3x3 boxes and leaves the gap between them zero. Therefore the rule is **not** one global box per color; it is one box per same-color 4-connected component.

Implementation: discover nonzero same-color components with 4-neighbor flood fill, then paint every cell of each component's bounding box on a fresh zero grid. This predicts query 1 will keep the two color-3 components separate.

No generator code, Racket rule, private labels, or prior solution text was opened during this solve. I had unavoidable earlier rule exposure from performing the assigned generator repair, so this is not claimed as blind.
