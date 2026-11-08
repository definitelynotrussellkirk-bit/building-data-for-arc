# Solve work log

I had already seen the task rule while repairing the assigned generator, so this
is an exposed post-repair solve rather than a blind inference record. During this
solve I used only the visible examples printed by `prepare`; I did not reopen the
Racket authority, generator source, private labels, or prior solution text.

## Revision 1 — normalize and subtract the two masks

Each input has two separated monochrome objects of unequal size. The output uses
the larger object's color. I translated each object independently so its own
bounding-box top-left becomes `(0, 0)`, then removed every normalized cell also
occupied by the smaller object.

The output canvas is not always just the larger object's box. Example 2 has a
three-row larger mask and a four-row smaller mask, while the output is four rows
tall. This indicates the canvas takes the maximum normalized height and width of
the two objects. Example 0 confirms exact-cell subtraction rather than deleting a
whole bounding rectangle: after removing the two vertical small-mask cells, the
remaining lower row and three-cell crossbar are retained.

The implementation therefore:

1. finds same-color four-connected non-background components;
2. sorts them by descending cell count;
3. normalizes both masks independently;
4. paints `larger_mask - smaller_mask` in the larger color on the maximum of the
   two normalized bounding boxes.

Remaining uncertainty is limited to unseen malformed domains such as tied sizes
or more than two objects; neither occurs in the visible examples, so the program
follows the demonstrated two-object domain.
