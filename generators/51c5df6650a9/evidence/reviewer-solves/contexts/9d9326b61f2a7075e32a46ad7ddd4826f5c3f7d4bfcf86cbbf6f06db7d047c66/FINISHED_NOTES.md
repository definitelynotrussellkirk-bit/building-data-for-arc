# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or the assigned repair generator before this
attempt. I used only the packet's visible challenge.

## Revision 1 — use the first row as a packing key

Every example has one isolated cell per foreground color in row 0. Reading those
cells left-to-right gives the output object order. The remaining cells of each
color form one object elsewhere in the grid. The output removes the row-0 key,
crops each object to its bounding box, preserves its internal shape, and packs
the crops left-to-right starting at output row 1 and column 0, with exactly one
background column between bounding boxes. All other cells are background and the
canvas dimensions stay unchanged.

Checks against the visible examples:

- example 0 key `6,3,4` yields the T, L-triomino, and tall-L crops in that order;
- example 1 key `8,9` yields the two four-cell crops with one blank column;
- example 2 key `7,6` yields the side-T then the zigzag crop.

For query 0 this predicts order `7,5,2`; for query 1, `6,7,4,2`. I assume one
key cell per color and one non-key object per keyed color. If an object itself
occupied row 0, excluding the entire first row would be ambiguous, but no visible
case does so and the key row is otherwise empty.
