# Blind solve work log — bdd177308a5b

## Observation and hypothesis

The upper-left object sits inside an L-shaped frame made of color 5. Across all
three visible training pairs, one remote monochromatic 4-connected object has
exactly the same normalized cell coordinates as that framed object, without
rotation or reflection. The output changes only that matching object's cells to
5; all distractor objects remain unchanged.

Examples checked manually:

- Pair 1: framed color-2 shape `[(0,0),(0,1),(1,0),(2,0)]`; color 7 is the
  same orientation and is recolored.
- Pair 2: framed color-1 T shape; color 3 is the exact translated copy.
- Pair 3: framed color-9 corner-plus-row shape; color 4 is the exact translated
  copy.

## Implementation

Locate the meeting point of the color-5 frame from its all-5 top/left prefixes,
normalize the nonzero/non-5 cells inside it, enumerate 4-connected same-color
components outside it, and recolor every exact same-orientation match to 5.

## Test predictions

- Test 1: color 7 matches the framed color-1 shape.
- Test 2: color 9 matches the framed color-1 shape.

No reference program, generator source, private labels, prior solution, or audit
record was consulted.
