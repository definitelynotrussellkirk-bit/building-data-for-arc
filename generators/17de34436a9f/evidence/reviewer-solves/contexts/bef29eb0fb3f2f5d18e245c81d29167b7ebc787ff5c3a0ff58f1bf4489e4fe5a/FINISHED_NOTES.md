# Solve notes

Earlier rule exposure exists because this is the required post-repair solve, but
this implementation was reconstructed from the visible challenge only. I did not
consult the generator, Racket source, reference solutions, prior solve directory,
or private labels during this episode.

## Hypothesis

Each input contains a single maroon `9` in one corner and one separate colored
shape. The output discards the marker/background margin, crops the colored shape
to its bounding box, and rotates the crop according to the marker corner.

The four visible examples determine the complete corner table:

- top-left: no rotation;
- top-right: 90° clockwise;
- bottom-right: 180°;
- bottom-left: 90° counter-clockwise.

The solution locates the marker, crops all nonzero/non-9 cells while preserving
zeros inside the bounding box, applies the inferred number of clockwise turns,
and returns the crop. One revision is sufficient if it reproduces all four
visible outputs.
