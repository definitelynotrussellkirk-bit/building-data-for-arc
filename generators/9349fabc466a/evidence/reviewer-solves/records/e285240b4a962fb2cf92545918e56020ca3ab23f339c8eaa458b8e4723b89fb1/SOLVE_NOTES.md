# Solve work log

## Prior exposure

I used only `solve/challenge.json` during this solve. I had already inspected this
assigned task's generator and canonical rule while repairing it, so earlier rule
exposure is **yes**; I did not consult either source, private labels, or hidden
answers after the solve episode was prepared.

## Visible-example rule

For each nonzero color, connect equal-colored markers that share a row or column.
A row containing at least two markers of that color is filled from its leftmost
to rightmost marker, and a column containing at least two is filled from its
topmost to bottommost marker. Unaligned markers remain unchanged. This explains
both two-marker segments and the four-corner rectangles in the training pairs.

At crossings, the lower numeric color is visible: color 7 beats 8 in training
example 1 and color 4 beats 5 in training example 3. The implementation therefore
renders colors from high to low so the lower color is written last. It uses the
original marker positions to decide all segments, preventing newly drawn cells
from creating additional lines.

The first test should contain a horizontal color-1 segment crossing a vertical
color-2 segment, with color 1 at the intersection. The second should contain a
color-1 rectangle, a vertical color-2 segment through it, and one unaligned
color-2 marker; color 1 should win both crossings.
