# Visible-only solve log

This is a human work log based only on `solve/challenge.json`. I had seen the task family earlier while reviewing the generator, so this is **not blind**; I did not reopen the generator, Racket rule, reference output, or private labels during this solve episode.

## Hypotheses from the three demonstrations

1. The output is cropped to the bounding box of all nonzero input cells. Training examples 1 and 3 preserve holes/empty cells inside that crop, while removing the surrounding zero canvas.
2. Foreground colors identify display regions, not separate objects for the transformation. In examples 1 and 3, differently colored cells touch and the depth-2/3 pattern crosses the color boundary. Therefore first convert every nonzero cell to one binary foreground mask.
3. For each 4-connected foreground component, assign onion depth: exposed boundary cells are 1; remove them; the next cardinal boundary is 2; continue inward. The 5×7 rectangle gives the expected nested 1/2/3 bands, distinguishing this from distance to the crop rectangle alone.
4. Disconnected foreground components are peeled independently but rendered together in the single global foreground crop. The second query contains two separated rectangles, so zeros between their bounding boxes must remain.

## Planned implementation

Find 4-connected components of nonzero cells. Repeatedly identify cells with at least one cardinal neighbor outside the remaining component, write the current layer number, remove that boundary, and increment. Finally crop the depth grid to the global foreground bounding box. The algorithm leaves interior zeros between disconnected components unchanged.

## Remaining uncertainty

The visible data contains colors 1–8 only, so I treat every nonzero value as foreground. The examples strongly identify cardinal, not diagonal, connectivity and peeling. I am making one direct solve attempt rather than manufacturing a failed revision.
