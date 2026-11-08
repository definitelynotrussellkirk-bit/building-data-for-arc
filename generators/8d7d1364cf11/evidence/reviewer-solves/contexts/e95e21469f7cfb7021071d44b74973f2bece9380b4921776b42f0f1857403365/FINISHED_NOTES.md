# Visible-only solve log

Earlier exposure to the repaired task semantics exists, so this is not a blind
record. During this solve I kept the generator, canonical rule, private labels,
and prior reference material closed and used only the three examples in this
solve episode.

## Hypothesis

- Color 4 is the background.
- Every 8-connected non-background component larger than one cell is a source
  template; every singleton is a marker/dot.
- A marker whose color appears in a source template requests a translated copy
  of that whole template, aligned so the same-colored source cell lands on the
  marker.
- The original templates and all markers are cleared; markers whose color is
  absent from all templates are decoys and leave no output.

This explains example 0's two translated copies and disappearance of the two
color-5 decoys. Examples 1 and 2 show multiple templates, rotated/irregular
shapes, multiple marker colors, and productive color 5, which rules out a fixed
shape, fixed location, or “5 is always noise” shortcut.

## Implementation

`solution.py` independently finds row-major 8-connected components, partitions
shapes from singleton dots, uses the first matching source cell in deterministic
row-major order, and stamps onto a fresh all-4 grid with bounds checks.
