# Solve notes

This is a human-readable work log based only on `solve/challenge.json` during
this episode. I had seen the task rule earlier while reviewing the generator, so
this is an exposed solve and will be declared as such.

## Hypothesis

Every nonzero input cell is a fixed colored seed. Each zero cell is assigned to
the seed with minimum Manhattan distance `|dr| + |dc|`. If two or more nearest
seeds have different colors, the output is 8. Existing seeds remain unchanged.

## Evidence from the visible examples

- In training example 3 the three seeds share the rightmost column. Entire rows
  become their nearest seed color; rows exactly midway become all 8, which is
  the expected Manhattan tie line.
- In training example 1 the left seed at `(5,0)` owns column 0 while the two
  seeds at column 3 form horizontal regions; the repeated 8 boundaries match
  equal Manhattan distances, not Euclidean distance.
- Training examples 2 and 4 contain diagonal stair-step boundaries, again
  matching Manhattan Voronoi cells.
- The output preserves every original nonzero seed.

## Implementation

Collect all nonzero cells as seeds. For each zero, compute every Manhattan
distance, take the minimum, collect the colors of all seeds at that minimum,
and write the sole color or 8 when the nearest-color set has size greater than
one. Return a fresh rectangular grid.
