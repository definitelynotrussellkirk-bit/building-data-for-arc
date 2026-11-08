# Solve notes

This is a human work log from the visible examples. I had earlier exposure to
the repaired generator family, so this is **not blind**; during this solve phase
I did not reopen or consult the generator, Racket source, private answers, or
previous solution explanations.

## Hypothesis

1. Ignore zero padding and crop to the nonzero bounding box `P`.
2. The crop has shape `ph × pw`; the answer has shape `ph² × pw²`.
3. Treat `P` both as a selector mask and as the tile. Divide the answer into a
   `ph × pw` grid of `ph × pw` blocks. A nonzero selector cell copies the exact
   multicolor crop into its corresponding block; a zero selector cell emits a
   zero block.

The multicolor visible examples distinguish this from recoloring each copied
block by its selector color: every emitted block preserves the full crop's
internal colors.

## Implementation

`solution.py` extracts the bounding box and computes each output cell directly:
use the block coordinates to decide whether the block is active and the within-
block coordinates to copy the crop value. The input is not mutated.
