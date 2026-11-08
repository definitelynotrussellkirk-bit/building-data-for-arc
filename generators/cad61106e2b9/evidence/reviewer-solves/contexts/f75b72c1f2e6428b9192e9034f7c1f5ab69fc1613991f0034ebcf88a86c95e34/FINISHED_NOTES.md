# Exposed solve work log

I inspected only `solve/challenge.json` for this solve. I had already reviewed the task earlier, so this is not a blind episode; I did not reopen the generator, Racket source, private labels, or previous solution text while solving.

## Visible-example hypothesis

All three demonstrations contain three disconnected hollow rectangles in color 4, nested largest to smallest, plus two isolated colored cells. One isolated value is in `1..3`; the other is a distractor outside that range.

The output preserves every original cell and paints some zeros with color 8:

- control 1 paints the region inside the largest frame but outside the complete bounding box of the middle frame;
- control 2 paints inside the middle frame but outside the complete bounding box of the smallest frame;
- control 3 paints the interior of the smallest frame.

Thus the control is a 1-indexed rank after sorting the color-4 rectangular frames by descending area. The distractor position/color is irrelevant. I implemented connected-component extraction so each frame is identified structurally rather than by assuming fixed coordinates or concentric spacing.

## Checks considered

The first query visibly contains control 1 near the bottom and distractor 9; it should fill the outer band. The second contains distractor 5 at `(0,0)` before control 2 in row-major order; this directly rules out “first singleton is the key” and should fill the middle band. The algorithm preserves frame borders, both singleton cells, and all nonzero cells.
