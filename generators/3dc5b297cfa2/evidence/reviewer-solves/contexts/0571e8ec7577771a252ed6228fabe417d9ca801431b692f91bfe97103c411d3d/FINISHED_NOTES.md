# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had already inspected the assigned generator and canonical rule while repairing it. During this solve phase I used only the visible examples printed by `solve prepare` and did not reopen the generator, Racket source, references, or private query labels.

## Revision 1

The modal color is the background. The remaining cells form one two-color object. In all three visible examples the two object colors exchange roles. The lower half of the object's bounding box stays at the same coordinates after the color swap, while the upper half, including the floor-midpoint row, moves right.

The displacement has a visible conditional. In the two examples containing black (`0`), the full object bbox is five columns wide but the nonblack object cells span only three columns; the upper half moves three columns. In the nonblack example, the upper half moves the full five-column bbox width. Therefore I use the horizontal span of nonblack object cells when black is one of the two object colors, and otherwise the full bbox width.

I implemented this directly from object coordinates: detect the modal background, collect the two non-background colors, compute the object bbox and midpoint, create a background-filled output, swap colors, and translate only cells at or above the bbox midpoint. Both visible queries contain black and therefore use the nonblack horizontal span. Remaining uncertainty is limited to malformed inputs or clipping, neither of which appears in the visible episode.
