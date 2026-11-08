# Visible-only solve notes

This is a human-readable work log based only on the three displayed training
pairs and two masked inputs. I had already inspected the selected generator and
canonical rule during the repair phase, so this is **not blind**; I did not
consult either source again after `solve_episode.py prepare`.

## Hypothesis

The last row is an ordered instruction strip. Tight-crop the single nonzero body
above it, then emit one transformed copy for each nonzero key cell:

- 2 and 5: unchanged body
- 3: rotate 90 degrees clockwise
- 4: rotate 180 degrees

Preserve key order, put one all-zero separator column between pieces, and
(top-)align all pieces in an output whose height is the tallest transformed
piece. Example 0 distinguishes the 3 and 4 transforms; examples 1 and 2 show that
5 is the same identity operation as 2 and that repeated codes produce repeated
pieces rather than being deduplicated.

## Implementation decision

I locate the body from all nonzero cells above the last row, crop to its bounding
box, transform a fresh copy for each key, and assemble a zero-filled output.
No query output or private label was inspected.
