# Blind solve notes — b9b63ae52d91

## Observation

The output preserves every zero. Each input `8` is recolored either `2` or `5`.

Comparing the top and bottom rows, then moving inward, showed an exact vertical-reflection rule:

- an `8` becomes `2` when the cell at the same column in the vertically mirrored row is also `8`;
- otherwise it becomes `5`;
- `0` remains `0`.

The middle row of an odd-height grid mirrors to itself, so every `8` there becomes `2`.

## Verification before submission

I checked the hypothesis against all five visible training pairs, including the 6x6 example that initially resembles detection of 2x2 blocks. Vertical reflection explains every colored cell, whereas the local-block hypothesis does not explain the larger examples.

No generator, Racket rule, reference solution, private label, or earlier explanation was consulted.
