# Blind solve notes — dc155169ea57

I inspected only `solve-blind/challenge.json` before writing the solution.

## Hypothesis 1

The full row of color 2 is a horizontal barrier under several color-1 objects on
an 8 background. Gravity acts downward on each four-connected color-1 object.
Objects wider than one column stop with their lowest cell immediately above the
barrier. Objects exactly one column wide puncture their column of the barrier and
continue until their lowest cell reaches the bottom edge.

Evidence from the visible lessons:

- In lesson 1, both vertical one-column bars move below the barrier and leave one
  barrier gap each, while the two-cell horizontal bar rests immediately above it.
- In lesson 2, two wider shapes preserve shape and rest above the barrier. The
  five-cell vertical bar bottom-aligns; because the grid has only three rows below
  the barrier, one final pixel lies above the barrier and the pixel coincident
  with the punched barrier row is absent.
- In lesson 3, a single pixel is a one-column object, so it punctures the barrier
  and falls to the bottom row.

## Implementation choice

Find the modal background, the monochrome non-background barrier row, and all
four-connected moving-color components above it. Clear original components.
Bottom-align width-one components against the grid, erase their barrier column,
and omit any translated pixel that lands on the barrier. Bottom-align all wider
components against the row above the barrier.

Potential ambiguity: the examples do not show collisions between independently
falling components. The implementation follows the demonstrated independent
component behavior and does not invent stacking rules.
