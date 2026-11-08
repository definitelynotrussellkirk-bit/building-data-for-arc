# Solve work log

Earlier exposure: none. I did not inspect any generator, Racket rule, canonical answer, audit evidence, or prior solution before this blind solve.

## Observation and hypothesis

The upper region contains one monochrome object, separated from a bottom command row by blank space. Each nonzero bottom-row cell produces one copy of the tightly cropped object, in left-to-right order. Copies are separated by one background column and top-aligned when rotations change rectangular dimensions.

Comparing visible outputs gives the command map:

- `2`: unchanged;
- `3`: rotate 90 degrees clockwise;
- `4`: rotate 180 degrees;
- `5`: unchanged in the only visible occurrence.

The duplicate unchanged codes are unusual, but command 5's visible tile is exactly the original asymmetric shape, so treating it as 270 degrees would contradict the supplied example.

## Test-first probe

I added `test_solution_visible.py`, which loads all three public training pairs and calls `solve`. Before implementation it failed with the expected `NotImplementedError` (`red-test.log`). I then implemented only the inferred crop/rotate/concatenate behavior.

Remaining uncertainty: command 5 has only one demonstration, so the direct observed mapping is used rather than extrapolating a numeric rotation sequence.
