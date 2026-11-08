# Post-repair visible-only solve notes

## Exposure declaration

I had already inspected this task's generator and selected rule while repairing it, so this is **not blind**. During this solve episode I used only the visible examples printed by `solve prepare` and did not reopen the generator, Racket source, reference solutions, or private labels.

## Hypothesis from the visible pairs

Every pair contains exactly one complete color-9 row or column. The output preserves the input and reflects every nonzero, non-9 colored cell across that line, including cells sourced from either side. Train 1 visibly requires both directions at once: the top color-7 object appears below, while the bottom color-2 object appears above. Train 2 similarly copies right-side objects to the left of a vertical axis.

## Implementation

1. Locate a full color-9 column; otherwise locate a full color-9 row.
2. Copy the grid.
3. Iterate the original cells, not the evolving output.
4. For each color outside `{0, 9}`, write it at the in-bounds reflected coordinate.

The explicit in-bounds test handles asymmetric axes where part of a reflected object would fall outside the canvas.
