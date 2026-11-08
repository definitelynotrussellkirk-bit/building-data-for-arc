# Solve work log

## Prior exposure

This is the required post-repair visible-only episode, not a blind solve. Before it was prepared I had already read and repaired this task's generator and had seen the canonical rule while doing source review. I therefore mark earlier rule exposure **yes**. During this solve episode I did not reopen the generator, Racket source, canonical pairs, private labels, prior solution explanations, or any reference implementation; I used only the displayed visible examples.

## Revision 1 — classify each monochrome component by bounding-box aspect

The examples show that input colors are discarded and each monochrome 4-connected component is recolored independently:

- bounding box wider than tall → red (`2`),
- bounding box taller than wide → green (`3`),
- square bounding box → yellow (`4`).

The occupied-cell mask is preserved rather than filling the bounding box. Train 0 is especially useful because color `8` appears in two disconnected components: the tall component at the upper right becomes `3`, while the short horizontal component near the bottom becomes `2`. Train 1 and train 2 contain irregular components whose holes/background remain background, confirming mask preservation.

Implementation: breadth-first search over same-color cardinal neighbors, compute each component's bounding-box height and width, then recolor only that component's existing cells according to the comparison. Different input colors that touch remain separate because connectivity also requires equal color.

Remaining uncertainty is limited to cases absent from the visible examples, such as diagonal-only same-color contact; cardinal connectivity is the simplest interpretation consistent with every shown component.
