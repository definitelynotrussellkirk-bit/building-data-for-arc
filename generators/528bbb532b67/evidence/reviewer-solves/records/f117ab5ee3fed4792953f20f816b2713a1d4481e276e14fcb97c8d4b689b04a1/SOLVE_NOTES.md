# Solve work log

No earlier exposure to this task's rule, generator, reference solution, private labels, or prior solve notes. I used only the visible examples in `challenge.json` and local tests against the visible training pairs.

## Observation and hypothesis

Every example contains a rectangular border of color 8. The non-border motif lies in the left half of the rectangle's interior. The output keeps the frame and original motif, then reflects the entire left half horizontally into the right half. For an even interior width, the axis lies between the two middle columns; for an odd interior width, the center column maps to itself. All motif colors are copied unchanged.

I compared coordinates in all three training pairs. In example 0, interior column 10 maps to 11 and column 7 maps to 14. In example 2, the seven-column interior has center column 9, which remains fixed while columns 6–8 map to 12–10. This ruled out simple translation and color-specific completion.

## Implementation and probe

I locate the color-8 frame by its bounding box, copy the input, and for each interior row reflect columns from the left edge through the midpoint using `mirror = left + right - column`. I intentionally copy zeros as well as colored cells so the reflected half exactly matches the source half rather than only adding colored pixels.

A temporary unit test imports `solution.py` and checks all visible training pairs. The untouched template first failed with `NotImplementedError`, then the implemented solver passed all three visible examples. Remaining uncertainty is limited to whether an unseen episode could place the source motif on the right instead; all visible evidence consistently specifies left-to-right reflection, so I kept the minimal rule rather than guessing an orientation detector.
