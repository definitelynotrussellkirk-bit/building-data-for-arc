# Post-repair visible solve

## Exposure and evidence boundary

This is a **post-repair exposed episode**: the parent reviewer saw the rule
during repair. I am a newly isolated visible-only solver, and my puzzle evidence
is limited to `solve/challenge.json`. These are distinct facts; this episode is
not described as blind. I have not consulted the generator, Racket rule,
canonical data, private labels, reference solutions, earlier explanations, or
other agents' reports. The earlier blind solve is unrelated and was not read.

## Initial observations and hypothesis

There are three visible training examples and two masked test inputs. Training
input/output dimensions are 4×6 → 12×12, 8×6 → 24×24, and 6×10 → 30×30.
The output side is half the number of input cells. Each input has even height
and width, so it can be partitioned into nonoverlapping 2×2 blocks.

The initial hypothesis is that these blocks are read in row-major order. The
first block becomes the central 2×2 square. Each subsequent block adds one
outer square ring, using its top-left, top-right, bottom-left, and bottom-right
values for the corresponding output quadrant's part of that ring. Equal
neighboring colors can visually merge consecutive rings.

Concrete first-example observations: the first block is `[[9,5],[7,6]]`, which
matches the central 2×2 square; the second is `[[4,2],[3,2]]`, which matches the
next ring; the last is `[[4,9],[9,6]]`, which matches the outer ring. The same
center and outer-ring reading is consistent with the other two examples.

## Implementation history

Version 1 implements the initial hypothesis directly: initialize each expanded
square with the new block's quadrant colors, then copy the previous square into
its interior. There have been no revisions or deliberately incorrect versions.

## Checks and stopping condition

Validation is pending the required checker run. No hidden query correctness
feedback is available. Stop when all visible examples fit and both masked inputs
execute, unless the checker exposes a concrete implementation problem.

## Limits

The visible evidence does not define behavior for odd input dimensions, empty
grids, or malformed grids. The implementation explicitly rejects odd dimensions
and nonrectangular grids. It treats all colors as values with the same role.
Matching visible examples cannot establish correctness on withheld outputs.
