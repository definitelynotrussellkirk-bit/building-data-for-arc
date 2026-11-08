# Visible-only blind solve

No generator, rule, canonical helper, notes, private labels, or earlier solution
explanations were opened before this attempt. Only the preparation command's
visible examples and query inputs were used.

## Hypothesis and probes

The nonzero top-left cell is a turn-count cue. Remove that cue, crop the remaining
object to its tight bounding box, and rotate the crop clockwise by that many
quarter turns. Preserve both object colors and background holes.

- Example 0: input 8 x 8, output 3 x 2. The corner is 1; a 2 x 3 L-shaped crop
  rotates once clockwise into the demonstrated 3 x 2 output.
- Example 1: input 8 x 8, output 3 x 3. The corner is 2; rotating its 3 x 3 crop
  180 degrees produces the displayed output.
- Example 2: input 7 x 7, output 2 x 3. The corner is 3; three clockwise turns of
  the 3 x 2 crop produce the displayed output.

The two query inputs are 7 x 9 and 9 x 10. Their output dimensions and labels
are unknown. Apply the same general crop-and-rotate procedure without using
query answers. No failed revision has occurred so far; no negative is fabricated.

## Limits

This hypothesis assumes the corner is an isolated cue and zero is background,
as in every visible example. It does not claim uniqueness among every possible
rule or correctness on the masked queries. The checker reports visible-example
agreement and execution only.
