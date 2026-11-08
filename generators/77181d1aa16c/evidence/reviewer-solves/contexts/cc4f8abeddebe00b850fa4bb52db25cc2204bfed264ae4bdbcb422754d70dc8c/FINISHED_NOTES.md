# Visible-only solve notes

Earlier exposure: yes. I had already inspected the assigned generator before this required post-repair solve, so this is not blind. During this solve I did not reopen the generator, Racket source, reference solution, private labels, or prior solution explanations.

## Hypothesis

The densest all-nonzero rectangle is a two-color source tile. The output places four versions of that tile in a local 2×2 frame: unchanged, left-right reflected, up-down reflected, and reflected both ways. Sparse nonzero cells outside the source are color-key indicators. Their positions identify a source role inside the corresponding reflected block, and their values give the replacement color for that role. A role without an indicator disappears. Example 0 has two indicators for the same upper-right role with different values; the output uses the first in row-major order.

## Implementation

I exhaustively locate the largest all-nonzero rectangle, rank its two colors by frequency, decode outside indicators through the local reflected coordinates, retain the first mapping for each `(block, role)`, then render the four-block frame on zeros. This also handles the rectangular source in visible example 3 and the shifted/edge-touching source in the test inputs.
