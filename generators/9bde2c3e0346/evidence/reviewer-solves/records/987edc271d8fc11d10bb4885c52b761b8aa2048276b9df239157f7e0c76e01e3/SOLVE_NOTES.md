# Visible-only solve notes

## Revision 1

Each same-color four-connected object is handled independently. Its output is the
one-cell-thick border of that object's axis-aligned bounding rectangle, rendered
on an otherwise zero grid. The examples distinguish this from a solid fill:
the center of the 3x3 color-4 object in train 0 and the centers of the 3x3
objects in trains 1 and 2 are zero in the output. They also distinguish identity
because missing border cells are added. I implemented component discovery and
painted only the top, bottom, left, and right edges of each bounding box.
