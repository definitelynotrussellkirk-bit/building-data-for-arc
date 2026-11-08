# Exposed solve notes — 4179e1ac3cf7

This is the required post-repair solve. I had earlier rule exposure during generator review, so this is **not blind**. During this solve phase I used only `solve/challenge.json`; I did not reopen the generator, Racket source, reference solutions, private labels, or prior explanations.

## Visible-example analysis

- Each input has one connected color-1 component and several connected color-3 components on a zero background.
- The color-1 component acts as a normalized-shape template; its absolute location is irrelevant.
- Only color-3 components whose four-neighbor shape exactly matches the template under translation survive.
- Surviving cells are recolored 8 on a fresh zero grid and horizontally completed within that component's own bounding box. Thus an asymmetric three-cell L can become a 2x2 cyan block, while a wider asymmetric component gains its missing reflected cells.
- Nonmatching green components disappear. A reflected-but-not-identical shape is still a nonmatch; matching is exact after translation, not up to reflection.

## Implementation plan

1. Extract four-neighbor components for colors 1 and 3.
2. Normalize each component by subtracting its top and left coordinates.
3. Select green components whose normalized cells equal the lone blue template.
4. For every selected component, paint each original cell and its left/right reflection around the component bounding box in color 8 on a blank grid.

No revision was made solely to manufacture a failure.
