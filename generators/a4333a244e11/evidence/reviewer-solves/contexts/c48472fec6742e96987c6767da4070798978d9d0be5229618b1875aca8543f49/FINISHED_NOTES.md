# Solve notes — a4333a244e11

This is a human work log for the post-repair visible-example solve. I had earlier
rule exposure from reviewing this task's generator, so this is not a blind solve;
I did not reopen the generator, Racket source, private labels, or any reference
solution during this episode.

## Visible-example hypothesis

All three examples retain the one-cell exterior and the color-8 rectangular
frame. Exactly two colored interior cells act as seeds. Every other interior
zero is colored by the seed with the smaller Manhattan distance; cells at equal
Manhattan distance remain zero.

Evidence from the visible examples:

- Example 0's diagonal seeds create a staircase boundary and preserved zero tie
  cells; Euclidean distance or a numeric-color tie break would not match it.
- Example 1 has seeds near the same side but still fills by taxicab distance,
  preserving the original seed colors rather than sorting colors by position.
- Example 2 has seeds in one row, producing a vertical zero bisector at exact
  ties.

## Implementation choice

Locate the bounding box of color 8, collect the two nonzero/non-8 interior seed
cells, and fill only interior zeros. Preserve the input shape, frame, exterior,
and seed cells. Leave ties unchanged. The implementation returns an unchanged
copy for malformed inputs rather than guessing.

No failed natural revision was needed; the first implementation directly tests
the rule supported by all visible examples.
