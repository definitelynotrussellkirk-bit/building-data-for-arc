# Blind solve notes — 2602c3d31d21

## Visible observations

- The rightmost occupied column contains one cell of each nonzero color, ordered top to bottom.
- Removing those cells leaves one spatial object per color.
- The output is a square table. With `n` legend colors, its side is `3n + 2`.
- Each legend entry appears as a 2×2 block along the top and left, with one zero separator row/column between blocks.
- Interior diagonal blocks are zero. Off-diagonal blocks are color 2 for congruent objects and color 5 otherwise.
- Congruence permits translation, quarter-turn rotations, and reflection. This accounts for the three-object class `{2,9,4}` and two-object classes `{7,5}` and `{1,6}` in train example 0, as well as `{4,5}` and `{9,8}` in train example 1.

## Hypothesis and implementation

1. Read the legend from the rightmost nonzero column.
2. Exclude the legend cells and collect each color's object cells.
3. Canonicalize every object over all eight dihedral transforms after translation to the origin.
4. Emit the labelled 2×2-block congruence matrix using fixed relation colors 2 (same shape) and 5 (different shape).

This predicts test-query classes `{8,4}` / `{1,7,5}` and `{5,7}` / `{9,3,1}` without consulting any generator or rule source.
