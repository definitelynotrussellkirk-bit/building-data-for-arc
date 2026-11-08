# Blind solve notes: fa3550d200a0

## Initial observations

- Each input contains one large, fully occupied rectangle. Its dominant color is the background of the desired output, and its rare non-background colors are anchor cells.
- Away from that rectangle are several small connected objects. Each small object contains blue (`2`) cells and one non-blue anchor color.
- For every anchor color present in the large rectangle, the output copies the relative blue-cell pattern from the detached object with the same anchor color and aligns the two anchor cells.
- Detached objects whose anchor color does not occur in the large rectangle are distractors and should be ignored.
- The output is exactly the cropped large rectangle after stamping the matching blue patterns.

## Implementation hypothesis

1. Find all 4-connected nonzero components.
2. Treat the largest component as the output rectangle and crop its bounding box.
3. Use the rectangle's most frequent color as its fill color; every other color in it is an anchor.
4. For each other component containing exactly one non-blue cell, compute every blue cell's offset from that component's anchor.
5. If the anchor color occurs inside the rectangle, stamp those blue offsets there. Ignore unmatched templates.

This directly explains all three visible examples, including the unmatched color-8 template in the first and unmatched color-1 template in the third.
