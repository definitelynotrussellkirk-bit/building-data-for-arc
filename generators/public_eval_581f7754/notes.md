# public_eval_581f7754 authoring notes

## Rule family

Every singleton foreground cell on the canvas border is a colored anchor. Each
remaining four-connected multicolor object contains a rare anchor-colored
marker. `assignment=matching_color` is canonical: move the whole object along
the axis perpendicular to the anchor side until its marker lies on the line of
the same-colored anchor. A completely filled 3×3 object whose marker is its
center also moves one cell toward that anchor side; this structural exception
preserves the supplied official labels without memorizing a grid.

`assignment=nearest_line` performs the same parsing and rendering but assigns
each object to the geometrically nearest anchor line, regardless of color,
with anchor reading order breaking ties.

## Sequential dependency

Stage A identifies anchors, marker cells, target sides, and one translation
vector per object. Stage B first erases every source object and then redraws all
of its colored cells from those vectors. Replacing the nearest-line assignment
vector with the matching-color vector changes the retained 30×30 witness.
