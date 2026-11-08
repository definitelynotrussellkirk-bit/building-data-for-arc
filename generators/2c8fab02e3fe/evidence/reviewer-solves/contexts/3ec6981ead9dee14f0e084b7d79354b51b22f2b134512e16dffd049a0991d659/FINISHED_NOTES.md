# Solve work log

This is a human-readable reasoning log based only on the newly prepared visible examples. I had already studied this task's rule while reviewing its generator, so this is an exposed post-repair solve rather than a blind solve. I did not reopen the generator, Racket source, canonical labels, earlier solve files, or reference solutions during this episode.

## Hypothesis

Every input contains a hollow rectangle made from color 8. Among all other nonzero colors, exactly one occurs once; that singleton is the key color. The output replaces every cell strictly inside the color-8 rectangle with the key color, including any repeated-color distractor already inside. The rectangle border and all cells outside it remain unchanged.

Evidence from the visible examples:

- Example 0: color 2 occurs once, while color 4 occurs twice inside the frame. The entire interior becomes 2, so frequency-max and preserve-existing-interior alternatives fail.
- Example 1: color 6 occurs once below the frame, while color 5 occurs twice with one copy inside. The entire interior becomes 6 and the outside 5 remains.
- Example 2: color 3 is the only non-frame foreground color and occurs once; it fills the interior.

## Implementation choice

Count colors to locate the unique non-{0,8} singleton. Compute the bounding box of all color-8 cells and paint only its strict interior. Copy the input first so outside cells and the border are preserved.

No failed natural revision was needed: the three demonstrations directly distinguish the singleton rule from the visible repeated-color alternatives.
