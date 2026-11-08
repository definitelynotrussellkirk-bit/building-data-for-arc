# Visible-only solve work log

## Hypothesis 1

Each input contains one connected color-2 object and isolated colored marker cells.
The output removes the source object and markers, then stamps the normalized source
shape in color 8 with each marker as the top-left anchor.  Marker color selects the
orientation:

- 3: unchanged
- 4: reflect left/right
- 5: reflect up/down
- 6: rotate 90 degrees clockwise

This matches all three visible pairs, including the third pair's two color-4
markers and the nonsquare source shape that distinguishes clockwise rotation.
I will implement the rule directly and check this first revision rather than add
an artificial negative attempt.
