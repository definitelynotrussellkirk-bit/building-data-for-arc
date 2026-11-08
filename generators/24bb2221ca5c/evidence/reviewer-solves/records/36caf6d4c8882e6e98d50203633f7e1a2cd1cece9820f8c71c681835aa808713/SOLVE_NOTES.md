# Blind solve notes — 24bb2221ca5c

## Visible pattern

Each nonzero 4-connected object acts as a wall. The output recolors only zero
cells in 4-connected holes enclosed by that object, using the object's color.
Zeros that can escape through a side gap remain zero. A missing *corner* does
not open a hole because diagonal contact does not connect background under
4-neighbor connectivity.

Evidence from the demonstrations:

- Both ordinary rectangular outlines become solid.
- The color-5 outline has a side gap, so its inner zeros remain connected to
  exterior background and it is unchanged.
- The color-9 outline lacks one corner, but its interior cannot reach that
  corner by an orthogonal path, so the interior is filled while the corner
  remains zero.
- The irregular color-8 outline likewise fills its enclosed pockets without
  replacing exterior zeros.

## Implementation

Find each 4-connected monochromatic component. Within its bounding box,
flood-fill all non-component cells reachable from the box perimeter. Recolor
original zero cells that were not reached. Components are detected from the
original grid, and output changes do not affect later topology.

## Expected test behavior

- First query: fill the interiors of both the 7 and 3 outlines.
- Second query: fill the color-4 interior (the missing bottom-right corner is
  only a diagonal opening); leave the color-6 object unchanged because its
  top-edge gap gives the whole interior an orthogonal path outside.
