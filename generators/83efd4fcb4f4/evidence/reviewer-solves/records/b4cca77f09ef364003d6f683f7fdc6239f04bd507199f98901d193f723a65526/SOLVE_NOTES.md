# Solve notes

## Visible-example observations

Across all five training pairs, the only changed cells are zeros replaced by color 8. Each changed zero is the center of a cardinal plus whose four immediate orthogonal neighbors are color 3. Zeros with only three cardinal 3-neighbors, diagonal-only arrangements, and unrelated colors 6/7 remain unchanged.

## Hypothesis

Copy the input. For every non-edge zero cell, change it to 8 exactly when its up, down, left, and right neighbors are all 3. Leave every other cell unchanged.

## Confidence checks from the visible pairs

- The rule accounts for every changed cell in all five examples.
- It does not rely on the number, placement, overlap, or boundary proximity of the pluses.
- It excludes the visibly present partial and diagonal decoys.
- Colors 6 and 7 are distractors and are copied unchanged.
