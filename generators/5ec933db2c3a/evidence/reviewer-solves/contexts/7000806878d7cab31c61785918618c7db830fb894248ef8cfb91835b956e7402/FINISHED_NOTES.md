# Solve work log

I had no earlier exposure to task `5ec933db2c3a`, its rule, generator, labels, or
solution material. I used only the prepared visible examples and local Python
experiments over `challenge.json`.

## Observation and hypothesis

Color 9 is a full-height vertical divider. The nonzero crop on its left is a
complete 3×3 key made from colors 2 and 7. The panel to the right is a 2×2 array
of 3×3 fragments at the four corners, separated by all-zero rows and columns;
the output drops the key/divider and preserves the right panel dimensions.

For every changed fragment, its already visible nonzero cells agree with one
rotation of the key and exactly two nonzero key cells are absent. The output
fills those two cells. Fragments missing one or three cells are left alone.

I first considered all eight rotations/reflections. A direct comparison showed
that every changed training fragment uses a rotation only (0°, 90°, 180°, or
270°). Allowing reflections creates ambiguous query completions that the
training transformations do not support, so the implementation deliberately
uses rotations only.

## Probe

I enumerated each training corner, compared its nonzero cells against every
rotation of the cropped key, and counted absent nonzero cells. The changed
corners all had one compatible rotation with missing-count 2; unchanged corners
had missing-count 1 or 3. Applying that rule reproduced all three visible
outputs exactly.

## Implementation

`solution.py` finds the all-9 divider, crops the left key, extracts the right
panel, checks its four key-sized corner fragments, and replaces only a fragment
with a unique compatible rotation having exactly two missing nonzero cells.

Remaining uncertainty: the visible data fixes the 2×2 corner layout and
rotation-only interpretation strongly, but private queries could in principle
exercise a symmetric key or a non-3×3 key. The code deduplicates symmetric
rotations and derives dimensions from the key rather than hard-coding 3×3.
