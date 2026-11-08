# Post-repair solve work log

This is a human work log based only on `solve/challenge.json` during the solve phase. I had already seen the task rule while reviewing the generator, so this is an exposed post-repair solve, not a blind solve. I did not reopen the generator, Racket rule, reference solutions, or private labels after preparing this episode.

## Visible-example observations

- Every input has one overwhelmingly frequent background color and one connected shape made from exactly two other colors.
- Every output swaps the two shape colors.
- The lower part of the shape stays in its original columns; the upper part moves right.
- The upper/lower split is based on the shape bounding box, not the whole grid: rows through `floor((r_min + r_max) / 2)` move, later rows stay.
- In the nonblack `1/3` training example, the horizontal move is the full shape bounding-box width (5 columns).
- In both training examples where black `0` is a shape color, the move is only 3 columns even though the full bounding box is 5 columns. Three is the horizontal span of the nonblack shape cells. This supports a black-specific shift exception rather than an arbitrary per-example offset.

## Revision 1 hypothesis

1. Detect the modal background.
2. Take all non-background cells as the shape and find its two colors and bounding box.
3. Swap the two colors everywhere.
4. Move cells in rows `<= floor((r_min+r_max)/2)` right by:
   - full shape-bbox width normally;
   - horizontal span of nonzero shape cells when black is one shape color.
5. Keep lower-half cells in place.

The two test inputs exercise both branches: test 1 is nonblack and should use full bbox width; test 2 contains black and should use the narrower nonblack span. The implementation is intentionally direct and does not rely on fixed grid size, fixed background, fixed colors, or a fixed shape location.
