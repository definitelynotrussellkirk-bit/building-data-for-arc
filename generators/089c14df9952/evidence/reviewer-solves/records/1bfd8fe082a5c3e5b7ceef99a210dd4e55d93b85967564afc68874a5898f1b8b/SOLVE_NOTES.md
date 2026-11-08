# Solve notes — visible examples only

This is a human-readable work log. I had already seen the generator's rule during
review, so this is an exposed solve, not a blind claim. During this solve phase I
used only the prepared visible examples and did not reopen generator, Racket, or
private-answer files.

## Hypothesis

Each separated nonzero object contains the same yellow-4 skeleton. One object is
the decorated base because it has the richest non-yellow palette (blue 1, red 2,
green 3). Every other object is a rotated/reflected copy of the yellow skeleton.
Copy every non-yellow base cell through the matching dihedral transform to each
target. An existing red-2 cell on a target is an orientation cue when the yellow
shape is symmetric. Decorations outside the board are clipped.

## Implementation plan

1. Extract 8-connected nonzero components.
2. Select the component with the most distinct non-yellow colors as the base.
3. Normalize its yellow skeleton and enumerate all eight rotations/reflections.
4. For each target, match the normalized yellow shape; when red is present, keep
   only transforms that place the base red marker on that red cell.
5. Stamp the complete transformed blue/red/green decoration in bounds.

The visible examples include symmetric red-hinted targets, asymmetric unhinted
targets, multiple targets, and edge clipping, so this one rule explains all of
them without a scene-level shortcut.
