# Solve work log

This is a human reasoning log based only on `solve/challenge.json`. I had earlier rule exposure during generator review, so this is an exposed solve; I did not consult a reference or private labels during this solve phase.

## Revision 1 hypothesis

Each nonzero same-color 4-connected object is processed independently. Within one object, inspect each column it occupies and fill zero cells from the object's highest cell to its lowest cell in that column. In other words, make each object vertically column-convex without filling horizontally and without joining disconnected objects that happen to share a color.

Visible evidence:

- Train 1 has two disconnected color-7 objects. Their internal column holes are filled, while the blank rows separating them remain blank, so the rule cannot be global per color.
- Train 2 fills the vertical holes inside the 4 and 6 shapes, while the already vertically convex 7 control remains unchanged.
- Train 3 fills gaps independently in the long 2, 4, and 9 objects, and leaves the already convex 8 object unchanged.
- Train 4 again contains two disconnected color-4 objects and fills each separately without bridging the empty rows between them.

Implementation: identify same-color 4-connected components, collect their rows by column, and paint only zeros between each column's minimum and maximum row. Existing nonzero cells are preserved.
