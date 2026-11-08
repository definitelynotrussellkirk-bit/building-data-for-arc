# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator and had seen the
selected rule before `prepare`. This is therefore an exposed post-repair solve,
not a blind solve. During this solve I did not reopen the generator, Racket
source, reference solutions, private query labels, or prior solution notes; I
used only the visible examples in `solve/README.md` / `challenge.json`.

## Revision 1 — aligned opposite-border pairs

Across all three visible examples, the color-5 cells form a rectangular frame.
A non-{0,5} color fills an interior column only when the same color occurs at
the aligned top and bottom positions. It fills an interior row only when the
same color occurs at the aligned left and right positions. Extra border markers
without a matching aligned endpoint remain unchanged.

Crossings reveal numeric overwrite order. In example 0, color 4's vertical line
survives crossings with rows 2 and 3. In example 2, color 8's vertical line
survives rows 1 and 2. This is consistent with processing colors in ascending
numeric order; within one color, columns then rows is harmless because the
color is the same.

Implementation: find the bounding box of color 5, copy the grid, iterate border
colors in ascending order, fill aligned top/bottom columns, then aligned
left/right rows. Remaining uncertainty is limited to unseen malformed inputs;
the visible task consistently contains one color-5 frame and preserves shape.
