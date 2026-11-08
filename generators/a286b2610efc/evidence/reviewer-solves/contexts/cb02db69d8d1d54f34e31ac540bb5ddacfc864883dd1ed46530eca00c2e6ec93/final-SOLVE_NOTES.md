# Fresh solve notes

## Visible evidence

- Train 1 and train 3 contain boundary-flush horizontal and vertical same-color pairs. Each pair gains the only available adjacent cell, becoming length 3.
- Train 2 is the discriminating example: both pairs are interior. The vertical pair at rows 2-3 extends to rows 1 and 4; the horizontal pair at columns 4-5 extends to columns 3 and 6. Each becomes length 4, so “always add exactly one cell” is false.

## Hypothesis

Scan every horizontal and vertical length-3 window in the original input. Replace the zero in `0,v,v` or `v,v,0` with `v`. Because an interior `0,v,v,0` pair belongs to two overlapping windows, both sides are filled. The conditions must read the original input rather than newly written cells, preventing cascaded growth.

## Predicted tests

- Test 1: horizontal 3-pair gains cells immediately left and right; vertical 4-pair gains cells immediately above and below.
- Test 2: bottom-left horizontal 6-pair and bottom vertical 1-pair each gain their sole in-grid extension.

## Implementation

Use an immutable copy for all pattern tests and a separate output copy for writes. Run horizontal and vertical scans over all length-3 windows.
