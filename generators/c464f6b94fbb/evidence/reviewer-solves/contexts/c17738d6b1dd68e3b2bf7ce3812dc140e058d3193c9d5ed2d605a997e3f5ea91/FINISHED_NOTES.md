# Solve work log

## Exposure declaration before solving

I had not opened task `c464f6b94fbb`'s generator, canonical rule, private labels,
reference solution, audit history, or any earlier explanation. I used only
`solve-blind/challenge.json` and local reasoning.

## Revision 1 — component crops sorted by occupied area

**Observation.** Each training input contains three isolated, single-color
objects on a zero background. The output removes their absolute positions,
crops each object to its bounding box, top-aligns the crops, and joins them with
one zero column. The object order is decreasing occupied-cell count:

- example 1: areas 6, 4, 1;
- example 2: areas 6, 4, 4, with the equal-area objects retaining top-to-bottom
  reading order;
- example 3: areas 8 (the hollow 3×3), 6, 4.

The hollow object rules out flattening objects to solid rectangles; exact pixels
inside each crop must be preserved. I considered sorting by height or bounding-box
area, but example 2 places a height-1 object before a height-2 equal-area object,
so height is not the primary key. Occupied area plus reading-order tie-breaking
explains every demonstrated order.

**Implementation.** Find monochromatic 4-connected components, crop each to its
bounding box, sort by `(-cell_count, top, left)`, and concatenate top-aligned
crops with one background column. An all-zero input returns an empty grid; that
case is not demonstrated and is irrelevant to the visible lesson.

**Expected test queries.** The first should order colors 3 (area 6), 9 (area 4),
6 (area 4). The second should order 9 (area 6), 5 (area 4), 3 (area 1).

**Remaining uncertainty.** The demonstrations do not distinguish equal-size
reading order from another tie-breaker correlated with position, nor 4-connected
components from grouping all pixels of a color. The supplied instances use one
connected object per color, so the chosen rule is the simplest supported one.
