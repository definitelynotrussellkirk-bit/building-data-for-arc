# Solve notes — fc999420d3aa

These are a human-readable work log based only on `solve/challenge.json` during
this solve episode. I had earlier rule exposure from reviewing this task's
generator, so this is not a blind solve; I did not consult the generator,
Racket rule, reference solutions, or private labels after preparing the episode.

## Visible-example inference

- Train 1 shows an upright T of color 2 becoming a five-cell plus by filling the
  zero directly below its center.
- Train 2 rules out a fixed direction: color 4 is missing its upper arm and color
  3 is missing its right arm; both are completed. The small color-6 structure is
  unchanged, suggesting the trigger requires exactly three existing cardinal
  arms rather than merely any partial shape.
- Train 3 confirms left- and down-missing cases and leaves a color-7 two-arm/L
  decoy unchanged.

Hypothesis: for each nonzero cell, inspect its four in-bounds cardinal neighbors
in the original input. If exactly three equal the center color and the remaining
one is zero, fill that zero with the center color. Apply all such fills
simultaneously and preserve everything else.

## Implementation choice

The solver first records all fills from the unmodified input and then applies
them to a deep copy. This avoids one completion creating a spurious second
completion during the same transformation.
