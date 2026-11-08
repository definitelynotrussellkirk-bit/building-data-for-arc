# Exposed post-repair solve notes

Earlier rule exposure: yes, because this is the assigned repair task. During this
solve episode I used only the newly prepared visible examples and did not reopen
the generator, Racket rule, reference solution, or private labels.

## Hypothesis

The top-left singleton is a key rather than part of the object. Remove it, crop
to the remaining nonzero bounding box, and then:

- key `1`: reflect the crop left-to-right;
- key `2`: reflect the crop top-to-bottom.

Evidence from the visible examples:

- Example 0 has key 1. Its 2x3 crop is `[[2,2,6],[6,0,0]]`; reversing each row
  gives the shown output.
- Example 1 has key 2. Its 2x4 crop is `[[4,4,1,0],[1,0,0,9]]`; reversing row
  order gives the shown output.
- Example 2 has key 1 and a tall 4x2 crop; reversing each row again matches,
  which rules out choosing the axis from the crop or canvas aspect.

The implementation applies that rule uniformly. No failed revision preceded
this one because all three visible demonstrations distinguish the relevant
axis shortcuts.
