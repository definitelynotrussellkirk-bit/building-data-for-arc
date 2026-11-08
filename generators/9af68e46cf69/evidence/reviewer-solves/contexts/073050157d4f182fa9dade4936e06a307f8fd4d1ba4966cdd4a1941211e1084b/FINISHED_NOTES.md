# Visible-example solve notes

The output preserves dimensions and every color-9 cell. Color-1 pixels split into
4-connected objects. The changed objects are exactly those that surround a
complete color-9 connected region: the whole object changes from 1 to 8.

I rejected the simpler “any 9 inside the bounding box” idea because the examples
include open, almost-ring objects whose bounding boxes contain 9 but whose interior
is connected to the exterior; those remain color 1. I also rejected “rectangular
rings only” because an irregular ring with an extra branch changes in the examples.

Implementation: find all 4-connected components of colors 1 and 9. For each blue
component, compute its bounding box and recolor it iff some entire maroon component
lies strictly inside that box. This uses only the visible examples. I had seen the
rule earlier during the assigned generator review, so this episode is not blind;
I did not consult the reference while writing or checking this solution.
