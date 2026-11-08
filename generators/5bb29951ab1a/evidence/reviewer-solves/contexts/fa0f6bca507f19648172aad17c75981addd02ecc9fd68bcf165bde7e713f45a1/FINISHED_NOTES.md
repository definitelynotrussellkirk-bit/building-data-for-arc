# Visible-only solve notes

## Evidence from the four demonstrations

Each input has background 0 and two nonzero colors. The more frequent nonzero color forms large rectangular blocks; the sparse color occurs as dots either inside those blocks, on their boundaries/gutters, or away from them. Every sparse dot disappears or is recolored to the block color, while all existing block-color cells and all background cells remain unchanged.

I compared the changed sparse dots against their four orthogonal neighbors in the original input. A sparse dot is recolored to the block color exactly when at least two orthogonal neighbors have the block color. Dots with zero or one such neighbor become background. This explains both interior holes and the straight bridge witnesses in the demonstrations, and it does not depend on palette or grid size.

## Implementation

1. Infer the block color as the more frequent nonzero color and the dot color as the other nonzero color.
2. Copy the input.
3. For each dot-color cell, count original-input block-color neighbors up/down/left/right.
4. Write the block color for count at least two; otherwise write 0.

No reference source was consulted during this solve. I had already inspected the task rule and generator during the assigned review, so prior exposure is declared `yes` at finish.
