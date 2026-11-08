# Solve notes

This is a human visible-example work log. I had earlier rule exposure from the
required generator review, so this is not a blind inference record; I nevertheless
used only `challenge.json` during this solve phase and did not consult the generator,
Racket rule, private labels, or reference explanations.

## Observations

- Outputs preserve the grid shape, all zero cells, all color-5 cells, and most
  orange (7) components.
- In training example 1, the orange component containing the bottom-left cell is
  recolored blue (1). The orange component near the bottom-right remains orange
  because it does not include the exact corner cell.
- Training example 2 is the key negative: the top-left component contains the
  exact corner and changes, while the lower-left component touches both the left
  and bottom borders but leaves the bottom-left corner empty, so it stays orange.
- Training example 3 repeats that distinction at the top-left: an L surrounding
  the corner but missing the corner stays orange. Exact top-right and bottom-right
  corner components change. The color-5 bottom-left marker remains 5.

## Hypothesis

Find each 4-connected color-7 component. Recolor the entire component from 7 to 1
iff at least one of its cells is one of the four exact grid-corner cells. Leave all
other colors and all other orange components unchanged. Connectivity is orthogonal,
not diagonal.

## Implementation

`solution.py` flood-fills every color-7 component, tests intersection with the four
corner coordinates, and recolors only qualifying components in a copied grid. No
special case depends on size, shape, bounding box, or merely touching borders.
