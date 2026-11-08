# Solve work log

## Exposure

I had not opened this task's generator, Racket rule, reference solutions, private
query labels, audit material, or earlier solution explanations. I used only the
visible examples emitted by `python3 review.py blind prepare`.

## Revision 1 — upper-left half of the nonzero bounding box

Across all three demonstrations, I first took the tight bounding rectangle around
all nonzero cells. The output is exactly its upper-left subrectangle, with each
side equal to the floor of half the corresponding bounding-box side:

- example 0: nonzero box `7 x 9`, output `3 x 4`;
- example 1: nonzero box `4 x 4`, output `2 x 2`;
- example 2: nonzero box `5 x 9`, output `2 x 4`.

Directly comparing cells confirmed that each displayed output equals that crop,
including zeros inside the crop; no recoloring or component filtering occurs.
I implemented that rule. An all-zero input is outside the observed domain; the
program returns an empty grid rather than inventing a location.

Alternatives considered were selecting a connected component or a color-frequency
pattern, but those do not explain the exact contiguous crops or output dimensions.
Remaining uncertainty is whether the intended wording is "top-left quadrant" of
a composite object, but the implemented geometric operation matches every visible
example exactly.
