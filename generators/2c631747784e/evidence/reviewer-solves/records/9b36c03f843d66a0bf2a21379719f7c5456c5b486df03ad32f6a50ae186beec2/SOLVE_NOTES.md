# Blind solve notes — 2c631747784e

## Attempt 1

Observed that color 8 is the background and every non-background cell belongs to one 4-connected, non-branching path. The occupied geometry is unchanged between input and output.

Hypothesis: read the colors from either endpoint along the path, reverse that sequence, and write it back onto the same cells. Endpoint choice is irrelevant because reversing a sequence and assigning it back produces the same coordinate mapping whichever endpoint starts the traversal.

Checks against visible examples:
- Example 1 path from `(7,5)` to `(9,2)` has input colors `0,1,7,5,9,5,7,2`; the output along those cells is exactly `2,7,5,9,5,7,1,0`.
- Example 2 similarly reverses `2,7,5,0,9,4,4,7`.
- The long third example is also a single path despite its multiple turns; spot checks at both endpoints and along the middle match full reversal.

Implementation probe: identify the modal color as background, compute 4-neighbor degrees among all other cells, start at a degree-1 endpoint, traverse the unique unvisited neighbor, reverse the gathered values, and write them back. Preserve the input unchanged if the occupied cells do not form a simple path rather than inventing behavior unsupported by the examples.
