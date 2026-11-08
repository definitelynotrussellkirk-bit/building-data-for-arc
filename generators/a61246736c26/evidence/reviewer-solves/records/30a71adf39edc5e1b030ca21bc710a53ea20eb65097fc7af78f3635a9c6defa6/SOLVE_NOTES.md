# Blind solve notes — a61246736c26

## Visible structure

The input is divided by full rows and columns of color 8. There are three
horizontal bands, identified by a color repeated in the extra far-left column
(5, 9, and 0 in the visible examples). Each band contains the same number of
framed tiles. The first tile region is one column wider only because it includes
the band label; after removing that column, every tile has the same dimensions.

For each vertical tile position, two bands contain the same shape encoded with
2 on an 8 background, while the remaining band contains a solid interior color
such as 3, 4, 6, or 7. The training outputs combine these ingredients:

- use the repeated 2/8 tile as the shape template;
- replace each 2 with the solid interior color from the third tile;
- replace the frame color 1 with the label color of the band that supplied the
  solid tile;
- retain 8 as background and insert one all-8 separator column between outputs.

## Probe before first checked revision

I wrote a local visible-only reconstruction test that applies `solve` to all
three training inputs and compares exact grids with their displayed outputs.
This test initially failed because `solution.py` was the prepared
`NotImplementedError` stub, then passed after implementing the rule above. The
implementation derives divider positions and tile sizes from the input rather
than assuming the 6x6 training size, because the first test query uses 5x5
output tiles.

## First hypothesis

The solid swatch selects both the output ink color and the output frame/owner
label; the duplicated patterned tiles provide redundancy and the geometry. I
expect this to handle all query columns independently.
