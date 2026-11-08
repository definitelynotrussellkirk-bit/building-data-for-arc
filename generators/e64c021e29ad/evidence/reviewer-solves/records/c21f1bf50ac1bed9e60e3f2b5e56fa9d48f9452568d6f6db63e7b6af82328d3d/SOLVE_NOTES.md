# Solve notes

## Hypothesis

The cells 1–4 are direction codes attached to the colored objects, rather than colors to preserve. Their meanings are consistent across the four visible examples:

- 1: up
- 2: right
- 3: down
- 4: left

For each 4-connected object of color 5–9, remove its code cell and extend every object cell in the coded direction through the corresponding grid edge. Preserve the object's own color in the swept region; all other cells are zero.

## Checks against visible examples

- Train 0: the code-2 object extends right and the code-1 object extends up.
- Train 1: code 2 extends the color-5 object right; code 3 extends the color-9 object down.
- Train 2 includes code 4 (left), code 3 (down), and code 1 (up), confirming all but code 2 independently.
- Train 3 again separates marker position from direction: the code value, not the side on which it touches, controls the sweep.

I implemented connected-component discovery, adjacent-code lookup, and cellwise ray painting. No reference or generator source was consulted during this solve phase; I had earlier rule exposure from the required generator review, so this is not a blind solve.
