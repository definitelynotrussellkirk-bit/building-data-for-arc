# Visible-only solve notes

## Observation

The first row contains three nonzero colors in left-to-right order; row 1 is blank. Color 5 forms closed rectangular walls below row 1. Each chamber contains between zero and three color-1 dots.

Across the three visible examples, a chamber with one dot is recolored to the first legend color, two dots to the second, and three dots to the third. A zero-dot chamber is also recolored to the third (last) legend color. The recoloring replaces every open cell in the chamber, including the dots, while the legend, separator row, and walls remain unchanged.

## Implementation

Starting at row 2, find 4-connected components of cells that are not color 5. For each component, count color-1 cells in the original input and fill the full component with `legend[-1]` for count zero or `legend[count-1]` for counts one through three.

## Exposure

This is the required post-repair solve, so I had already seen the task rule during generator review. During this solve episode I used only the visible challenge presentation and did not reopen the generator, Racket source, canonical data, or private labels.
