# Post-repair solve notes

This is a human work log from the visible examples only. I had already seen the
assigned task's rule while reviewing its generator, so this episode is not blind;
I did not reopen the generator, Racket rule, reference solutions, private labels,
or earlier solution explanations during the solve phase.

## Hypothesis

Each example contains three separated nonzero objects. Their original colours,
scan positions, and absolute sizes vary. The output keeps every occupied cell in
place, clears the background to zero, and recolours by **ascending occupied cell
count**: smallest object -> 2, middle -> 3, largest -> 4.

Evidence from the visible examples:

- Example 0 has object areas 4, 5, and 6 and outputs colours 2, 3, and 4.
- Example 1 deliberately reverses spatial order: areas 12, 10, and 7 become
  colours 4, 3, and 2, so scan order and input colours do not determine rank.
- Example 2 uses one input colour for all objects; areas 7, 9, and 12 still map
  to 2, 3, and 4, so components must be identified geometrically.

## Implementation choice

Use same-colour 4-connectivity to extract nonzero components, sort components by
cell count, then paint them on a zero grid using 2, 3, and 4. Preserve the input
shape. No failed natural revision was needed because the three demonstrations
jointly distinguish the intended ranking from the obvious position and colour
alternatives.
