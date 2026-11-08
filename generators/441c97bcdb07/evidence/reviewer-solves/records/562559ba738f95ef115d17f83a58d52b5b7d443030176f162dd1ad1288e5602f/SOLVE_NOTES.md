# Solve notes

## Exposure disclosure

I had already inspected and repaired the generator before this solve episode, so this is **not** an independent blind reconstruction. I did not consult either Racket rule or private labels during the solve episode.

## Visible-example hypothesis

Each input has three identical, same-colored, 4-connected objects. Their top-left origins occupy three corners of an axis-aligned rectangle: top-left, top-right, and bottom-left. The output preserves those objects and places a translated fourth copy at the unoccupied bottom-right corner.

The examples also refute a color-count-only rule: object shape varies (3, 4, and 5 cells), while the output always adds exactly one complete copy. The implementation therefore detects components, normalizes each shape by its bounding-box origin, locates a unique group of three copies spanning two origin rows and two origin columns, and fills the missing Cartesian-product corner.

## Stopping reason

The same structural hypothesis explains all three visible demonstrations without special-casing dimensions, color, orientation, or cell count. I made one check attempt with this general component-based implementation.
