# Fresh solve notes for `1ce259f214c8`

This is a human work log written from `solve/challenge.json` only during the solve phase. I had already seen the task rule while reviewing the generator, so this is **not a blind solve**; I will declare earlier exposure as `yes`. I did not consult the Racket source, generator, reference solution, or private labels after `prepare`.

## Visible structure

Each input has one full-height gray (`5`) column. It divides the grid into equal-width left and right panels, while each output has exactly one panel's dimensions. The nonzero object colors vary across examples, but every output uses only `0` and `8`, suggesting that relative occupancy rather than source color is relevant.

## Hypotheses checked against the three demonstrations

1. **Union / OR of panel occupancy.** Rejected. In training example 2, several relative coordinates are occupied on both sides but the output is `0`; OR would color them.
2. **Intersection / AND.** Rejected. The outputs contain `8` at coordinates occupied on only one side, which AND would leave blank.
3. **Copy one panel or subtract only one direction.** Rejected. Training examples contain output cells unique to each of the two panels, so neither fixed source side nor a single directional difference explains all `8`s.
4. **Exclusive OR of occupancy.** Retained. At every visible coordinate, the output is `8` exactly when one panel is nonzero and the other is zero; it is `0` for both-empty and both-occupied coordinates.

## Revision 1

Implemented occupancy XOR. The solver locates the full-height gray divider instead of assuming a fixed width, verifies equal panel widths, ignores the particular object colors, and returns cyan (`8`) for unequal occupancy.

## Stop decision

Revision 1 passes all 3/3 visible demonstrations. The rule is dimension-general, color-agnostic, and the visible examples already exercise overlap plus both exclusive directions, so no additional revision was justified. Masked-query labels remain withheld as intended.
