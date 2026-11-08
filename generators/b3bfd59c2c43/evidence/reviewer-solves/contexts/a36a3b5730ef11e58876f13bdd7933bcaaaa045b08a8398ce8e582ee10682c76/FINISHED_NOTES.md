# Post-repair solve work log

## Exposure declaration

I had already inspected this task's generator and canonical rule while performing the assigned review, so this is **not a blind rule-discovery episode**. During this solve phase itself I used only `solve/challenge.json` and the solve checker; I did not reopen the generator, Racket reference, private query labels, or earlier solution files.

## Revision 1

### Visible pattern

Across all three training pairs, each nonzero object keeps any cell that is completely surrounded on its four cardinal sides by nonzero cells. Every nonzero cell touching background in at least one cardinal direction changes to color 8. Background remains 0. This behavior applies independently to every object and preserves the original color only in an object's fully enclosed core.

### Implemented hypothesis

For each nonzero input cell, inspect up/down/left/right in the **original input**. Recolor it to 8 when any such neighbor is background or outside the grid; otherwise retain the original color. The computation is simultaneous rather than an iterative erosion, so newly recolored boundary cells do not expose a second layer.

### Alternatives rejected from the visible examples

- **Recolor the entire component:** contradicted by preserved interior cells in the large square/rectangle and larger diamond-like objects.
- **Draw only each component's bounding-box perimeter:** contradicted by sloped and concave/irregular boundaries whose exposed cells are not just a rectangle frame.
- **Use eight-neighbor exposure:** contradicted by cells that have diagonal background but four nonzero cardinal neighbors and therefore keep their original color.
- **Iteratively peel layers:** contradicted by the single-step outputs, which retain the original core after only the initially exposed layer is recolored.

### Remaining uncertainty before check

None material: all visible examples are explained cell-for-cell by a single local four-neighbor rule, including objects at/near canvas edges.
