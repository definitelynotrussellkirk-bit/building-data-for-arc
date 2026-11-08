# Post-repair solve work log

This is an exposed solve: I had already reviewed the generator and intended rule before this episode. During the episode I used only the visible examples and did not reopen the generator or reference implementation.

## Hypothesis

Colors 2, 3, and 4 define an oriented local coordinate frame: 2 is the origin, the vector from 2 to 3 is local `u`, and the vector from 2 to 4 is local `v`. Colors 5, 6, and 7 define the target frame in the same order. Every color-8 cell is converted to signed `(u,v)` coordinates relative to the source frame, then a new color-8 cell is placed at the same coordinates in the target frame. Existing cells are preserved.

The frames are cardinal and orthonormal, so dot products with the source basis recover the local coordinates exactly. Applying those coordinates to the target basis handles rotations and reflections uniformly.

## Implementation choice

Locate the six singleton marker colors and all existing color-8 cells, recover the two bases, transform each motif cell, and paint the target copies into a cloned grid. No special cases are used for any particular orientation, motif size, or grid dimensions.
