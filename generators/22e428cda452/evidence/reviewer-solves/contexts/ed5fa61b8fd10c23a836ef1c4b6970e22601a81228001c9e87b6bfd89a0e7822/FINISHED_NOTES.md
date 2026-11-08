# Solve work log

## Exposure declaration

I had already inspected the selected generator and canonical rule while repairing it before this required post-repair solve. I therefore cannot treat this as a blind inference record; `earlier-exposure` must be `yes`. During the solve phase itself I kept the generator, Racket rule, reference solutions, private labels, and prior solve records closed and used only the visible challenge presentation.

## Revision 1 — side-specific inward corner projection

### Visible evidence

- Train 0 has one marker at the top-right corner. The corner is erased and its color appears as an inward 2×2 square, one-cell margin from the top and right edges.
- Train 1 has one marker at the bottom-left corner. The corner is erased and its color appears as a three-cell bent diagonal: relative inward offsets `(3,2)`, `(2,2)`, `(1,3)` from that corner.
- Train 2 combines top-right, bottom-left, and bottom-right markers. Every marker acts independently, preserving its color. The top marker again produces a 2×2 square, while both bottom markers produce mirrored bent glyphs.

### Hypothesis implemented

For each non-background corner marker:

1. erase the source corner;
2. choose signs pointing inward from that corner;
3. for a top marker, paint the four offsets `(1,1)`, `(1,2)`, `(2,1)`, `(2,2)`;
4. for a bottom marker, paint `(3,2)`, `(2,2)`, `(1,3)`;
5. mirror horizontal offsets for right corners and vertical offsets for bottom corners.

The two visible queries exercise two top markers together and one bottom-right marker. The implementation handles all four corners and multiple colors rather than hard-coding those grids.

### Alternatives rejected from visible examples

- A single glyph for every corner fails because top and bottom examples have different cell counts and geometry.
- Copying rather than moving fails because every visible source corner becomes background.
- Rotating one common glyph for all corners fails because the top output has four cells while the bottom output has three.

### Remaining uncertainty

The visible inputs place non-background cells only at corners and use 7 as background. I assume the generated domain preserves that grammar. The exact visible coordinates are unambiguous, so I am submitting this first revision without an intentional negative probe.
