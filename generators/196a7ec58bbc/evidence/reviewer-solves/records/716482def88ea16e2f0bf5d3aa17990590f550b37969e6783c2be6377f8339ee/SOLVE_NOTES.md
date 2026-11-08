# Solve work log

## Exposure declaration

I had earlier exposure to the generator and canonical transformation while repairing this task. During this solve episode I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solve notes; I used only the visible examples in `solve/README.md`.

## Visible-example inference

Each output is twice the input height and width. Splitting an output into four input-sized quadrants gives:

- top-left: the input unchanged;
- top-right: the input rotated 90 degrees clockwise;
- bottom-left: the input rotated 90 degrees counterclockwise;
- bottom-right: the input rotated 180 degrees.

I checked that decomposition against all three visible training examples. The third example is especially useful because its unequal colors distinguish reflection from rotation. The implementation composes exactly those four quadrants and rejects empty or non-square inputs, matching the visible domain.

## Alternatives considered

A reflection-based four-quadrant construction can imitate symmetric examples, but it fails on the asymmetric 2×2 training example. No private feedback or reference output was consulted.
