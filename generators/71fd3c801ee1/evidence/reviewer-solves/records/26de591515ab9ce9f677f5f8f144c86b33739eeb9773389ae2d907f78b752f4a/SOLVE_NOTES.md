# Solve notes: 71fd3c801ee1

## Visible-example hypothesis

Treat every nonzero 4-connected same-color region as one object. The output keeps the grid and all object geometry fixed, but recolors selected whole objects to `8`.

The selected objects are not necessarily identical outlines. Across the three visible pairs, the recolored objects share the same complete feature signature:

1. number of occupied cells (area),
2. number of enclosed zero regions (holes), and
3. reflection-symmetry class: neither, horizontal-axis only, vertical-axis only, or both.

Every object whose complete signature occurs more than once in that grid is recolored to `8`; objects with a unique signature retain their original color.

## Implementation

`solution.py` extracts 4-connected monochrome objects, normalizes each shape to its bounding box, counts enclosed background components, tests horizontal and vertical reflection symmetry, counts signatures, and recolors all members of repeated signatures.

## Exposure disclosure

This is the required post-repair exposed solve. I used only `solve/challenge.json` during the solve episode, but I had necessarily seen the rule and generator earlier while repairing the assigned task; that earlier exposure is declared at finish.
