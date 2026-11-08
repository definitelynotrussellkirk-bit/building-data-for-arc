# Blind solve notes — task 17b682bce66f

## Visible observations

- Every input has one pattern made from color 8 around a single color-9 cell,
  plus one or more isolated cells whose colors are in 2–5.
- The output removes the 8/9 pattern and keeps the 2–5 cells.
- Around a color-4 cell, the 8-mask appears rotated 180 degrees and recolored
  6.  This is exact in training examples 1 and 2.
- Around color 2, the unrotated mask is recolored 4.  Apparent missing cells
  are explained by overlaps with later stamps or by an original anchor.
- Around color 5, the mask is rotated 270 degrees clockwise and recolored 7.
- Training example 3 supplies the missing color-3 case: its mask is rotated
  90 degrees clockwise and recolored 5.

## Hypothesis

Treat 9 as the origin of the 8-cell mask.  Each target anchor color `c` in
`{2,3,4,5}` stamps that mask after `c-2` clockwise quarter-turns and recolors
it to `c+2`.  Higher anchor/fill colors win stamp overlaps, while original
anchors are restored last and always remain visible.  Cells outside the grid
are clipped.

## Cross-checks before running the checker

- Training 1, color 5: rotating the four 8 offsets 270 degrees places orange
  at the three cells on row 7 plus row 8 column 2; the color-2 anchor masks the
  fourth row-7 cell exactly as shown.
- Training 3: color 2 predicts five yellow cells, color 3 overwrites two with
  gray, and color 5 overwrites the shared central cells with orange; the union
  matches every nonzero output cell.

No reference material, generator source, private label, or prior explanation
was consulted.
