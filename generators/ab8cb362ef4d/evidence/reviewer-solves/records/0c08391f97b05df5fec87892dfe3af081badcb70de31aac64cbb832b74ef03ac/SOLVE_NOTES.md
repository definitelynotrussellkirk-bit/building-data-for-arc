# Post-repair solve notes

This is an exposed solve: I had already reviewed the task's generator and rule,
so the final declaration must say `earlier-exposure yes`. During this solve I
read only `solve/challenge.json`; I did not reopen the generator, Racket source,
canonical labels, private query outputs, or earlier solution explanations.

## Hypothesis from the three visible pairs

Each four-connected color-5 component identifies a rectangular box by its
bounding box. The output starts as zeros, repaints the entire bounding-box
border with 5, and applies vertical gravity separately to each interior column:
collect its nonzero values top-to-bottom and place them in the bottommost cells
without changing their order.

Evidence visible in the examples:

- Multiple boxes are transformed independently.
- A non-5 value can replace a border 5 in the input; the output repairs that
  position to 5 rather than treating it as an interior falling value.
- Several values in one column preserve their vertical order after falling.
- Empty space outside all box bounding boxes remains zero.

I implemented that rule directly with four-connected component detection and no
shape- or position-specific constants.
