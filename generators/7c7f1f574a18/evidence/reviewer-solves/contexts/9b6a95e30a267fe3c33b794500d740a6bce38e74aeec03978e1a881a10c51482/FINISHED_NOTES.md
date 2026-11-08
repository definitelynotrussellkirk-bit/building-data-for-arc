# Solve notes

The visible pairs contain separated non-background objects. Each object retains its exact cells and row position, but moves horizontally and changes color.

Objects with closed topology—solid rectangles and shapes containing a genuinely enclosed background region—move flush to the left and become red (2). Objects with a break whose internal-looking gap reaches the edge of the object's bounding box move flush to the right and become green (3). This is not simply “has a hole”: a broken frame has background inside its bounding box, but that background connects to the bounding-box boundary, so it is open.

Implementation:
1. Treat the unique modal color as background.
2. Extract 4-connected same-color non-background components.
3. For each component, inspect background cells in its bounding box. It is closed if the box is full, or if at least one gap component does not touch the bounding-box boundary.
4. Repaint closed components 2 and left-align them; repaint open components 3 and right-align them. Preserve vertical coordinates and shape.

This solve was written from the visible challenge pairs during the recorded episode. The reviewer had earlier rule exposure from repairing the assigned generator, which will be disclosed at finish; no hidden/reference labels were consulted during this solve.
