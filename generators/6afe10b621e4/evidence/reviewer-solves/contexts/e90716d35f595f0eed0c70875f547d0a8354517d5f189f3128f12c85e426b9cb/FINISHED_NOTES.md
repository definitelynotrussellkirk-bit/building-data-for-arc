# Blind solve notes — 6afe10b621e4

## Visible-pattern analysis

The inputs contain several disconnected objects in color 2, several in color 3,
and one color-8 singleton.  The outputs discard everything except one object of
each of colors 2 and 3.  Comparing all three training pairs suggests the retained
object is the largest 4-connected component of that source color.  The selected
color-3 component is recolored 1; the selected color-2 component is recolored 4.
The color-8 singleton and all unselected objects become background.

Checks against the examples:

- Train 1: color 2 sizes are 1, 3, 4; size 4 is output in color 4.  Color 3
  sizes are 5, 6, 3; size 6 is output in color 1.
- Train 2: the lower color-3 component (size 7) and the five-cell color-2 cross
  are the largest components and are exactly the output objects.
- Train 3: the central color-3 component and lower color-2 component are the
  largest and match the output.

## Test predictions

- Test 1: retain the six-cell sloping color-2 object near the top-middle as 4;
  retain the four-cell color-3 square at left as 1.
- Test 2: retain the large color-2 object at right as 4; retain the four-cell
  color-3 object around rows 8–10, columns 5–6 as 1.

No reference implementation, generator source, private labels, or prior solution
was consulted.
