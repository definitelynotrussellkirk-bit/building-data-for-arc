# Visible-only solve notes

## Observation

Each example has a full row of color 9 dividing a four-row header from a sparse lower board. In the header, full color-9 columns split several panels. Each panel contains a small multicolor object. The lower board contains isolated cells whose colors match one special color in a panel.

Comparing the first training pair:

- The lower color-4 marker becomes the complete panel containing 4, preserving that panel's colors and shape.
- The color-3 marker similarly expands to its panel.
- Two color-1 markers both receive the same panel, showing the operation is a reusable dictionary lookup rather than a one-time move.

Within every panel, the marker/key is the unique minimum color. Its position is the anchor: all other panel cells are copied at the same row/column offsets around each matching lower marker. The output is blank except for the union of these stamped prototypes. The examples also indicate ordinary in-bounds clipping if a relative cell would leave the lower canvas.

## Implemented hypothesis

1. Find the full color-9 divider row.
2. Split the header at full color-9 columns.
3. For each panel, collect nonzero cells; use the unique minimum color as the key and anchor.
4. Scan the lower board. At every cell matching a key, stamp the whole panel into a blank lower-sized output using anchor-relative offsets.

This single rule explains all three visible training pairs, including repeated keys, different panel widths, different anchor positions, and multicolor preservation.

## Exposure declaration

I had earlier exposure to this task's generator/rule during the assigned repair. During this solve episode I used only `solve/challenge.json` and did not reopen the generator, Racket source, private labels, or reference solutions.
