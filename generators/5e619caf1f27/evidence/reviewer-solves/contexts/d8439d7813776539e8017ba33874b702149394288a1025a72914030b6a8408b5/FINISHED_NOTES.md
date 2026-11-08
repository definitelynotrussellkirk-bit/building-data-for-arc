# Solve work log

No task-specific rule, generator, private label, or earlier solution was consulted.
Before this solve I had only read the packet's general workflow documentation.

## Revision 1 — alternating rectangular layer

Visible examples contain one nonzero rectangular object with two colors.  One
color forms the current outer layer; the other forms a rectangular inset.  Each
output preserves the object and adds a new rectangular layer outside it in the
inset color.

The added layer thickness is not globally fixed.  I measured the four distances
from the inset color's bounding box to the object's bounding box.  Three examples
have margins whose mode is 2; the example with margins `(1, 1, 1, 2)` adds a
1-cell layer.  This supports using the modal margin as the layer thickness, with
the nonmodal side reflecting the rectangular dimensions rather than a different
operation.

The implementation finds the nonzero bounding box, selects the color strictly
inside it, takes the mode of its four margins, and paints that many cells around
the existing box while preserving the original.  It clips safely at the canvas
edge, though all visible examples leave enough room.  Remaining uncertainty is
only tie behavior for synthetic cases where the four margins split 2–2; the code
uses a median-like deterministic fallback.
