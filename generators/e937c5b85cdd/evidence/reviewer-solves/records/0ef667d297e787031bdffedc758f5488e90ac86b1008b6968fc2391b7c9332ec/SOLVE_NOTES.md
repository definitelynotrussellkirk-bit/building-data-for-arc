# Solve work log

## Prior exposure

I had not opened this task's generator, canonical rule, private labels, prior
solutions, or audit records. I only read the packet instructions and the public
visible examples produced by `solve_episode.py blind prepare`.

## Revision 1 — asymmetric-cross direction markers

Observation: every non-background object is an orthogonal cross with one arm
longer than the other three. In every training pair, the output preserves the
interior and changes two cells of the outer color-6 frame along the cross
centreline. The object's color appears on the side opposite its longest arm,
and
zero appears behind the longest arm. Examples: train 0's color-9 cross has its
long arm to the right, so 9 is placed on the left frame and 0 on the right;
train 1's color-5 cross has its long arm upward, so 5 is placed on the bottom
frame and 0 on top.

Implementation: find the frame from the corner color and the background as the
most frequent interior color; collect each remaining same-color component;
choose its strongest four-neighbour junction as the cross centre; measure the
four contiguous arm lengths; treat the unique longest arm as the tail; write the
component color to the opposite frame and 0 to the tail-side frame.

Probe: a local visible-training harness first failed on the untouched
`NotImplementedError`, then was rerun after implementing this rule. Remaining
uncertainty is limited to malformed components or tied arm lengths, neither of
which occurs in the three visible examples.
