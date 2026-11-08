# Solve work log

Earlier exposure: none. Before this blind episode I had not opened this task's
generator, Racket rule, notes, solutions, private labels, or prior review records.

## Revision 1 — template stamping from isolated anchor pixels

The visible examples contain one or more nonzero multi-cell shapes and isolated
pixels whose colors each occur once inside one of those shapes. In every output,
the original multi-cell shape remains, while an exact translated copy appears at
each isolated pixel of the matching color. The matching-color cell is the
translation anchor. For example, in the first training pair the shape containing
color 1 is copied to the isolated 1, and the different shape containing color 5
is independently copied to the isolated 5.

I implemented nonzero 8-connected components because diagonal contacts are part
of the visible shapes. Singleton components are targets. A larger component is a
candidate template when it contains exactly one cell of the singleton's color
and at least one other color. The whole template is translated so that its anchor
cell lands on the singleton. The input is copied first, so source templates stay
in place. Bounds checks make the implementation total, although all visible
stamps fit the canvas.

Remaining uncertainty: if a future grid offered two different templates with the
same unique anchor color, the examples do not specify a tie-break. The code uses
the larger component; no visible pair requires that choice.

## Revision 2 — red anchors mirror horizontally

Revision 1 passed 2 of 3 visible pairs. Comparing my output with the visible
second training output showed that both copies made from isolated color-2 cells
had the correct shape and anchor but appeared on the opposite horizontal side.
The source red-anchored template has green cells at offsets `(-1, 0)`, `(0, 1)`,
and `(0, 2)`; the visible copies require `(-1, 0)`, `(0, -1)`, and `(0, -2)`.
The color-9 template in the same pair and all odd-colored anchors in the other
pairs preserve orientation, so this is not a global mirror.

I revised the rule to horizontally reflect offsets only when the anchor color is
2 (red). This is the narrowest rule supported by the examples and is directly
relevant because both test instances use red anchors. A numeric parity rule would
fit the shown anchor colors too, but treating ARC colors as semantic categories
rather than numbers is less speculative.
