# df3c6021b715

An 8–18 by 8–18 zero-background grid contains exactly two distinct nonzero
interior dots: one above row `floor(h/2)` and one at or below that integer
midpoint.  The selected rule sorts the dots by row, then paints a two-colour
frame: the upper dot colour fills the top edge, the upper dot's row, and both
side columns for rows `< floor(h/2)`; the lower dot colour fills the lower
dot's row, the bottom edge, and both side columns for rows `>= floor(h/2)`.

The v3 sampler exposes seven exact, observable axes (height, width, ordered
colour pair, two row slots, and two column slots) and a four-profile teaching
schedule.  The schedule retains canonical 10×10 anchors while deliberately
refuting fixed-row, ascending-colour, and fixed-row-5-split shortcuts.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
