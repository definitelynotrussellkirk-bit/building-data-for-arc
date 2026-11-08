# Solve work log

This is a human-authored work log based only on `solve/challenge.json` and local
Python calculations over those public grids. I had already seen the task's rule
while reviewing the generator before this solve phase, so this is **not blind**.
During the solve phase I did not open the generator, Racket source, reference
solutions, private labels, or prior solution explanations.

## Public-example analysis

I measured the nonzero bounding box in each visible training input and compared
it with the output. In all four pairs:

- the canvas dimensions are unchanged;
- every nonzero value and every relative `(row, column)` offset inside the motif
  is unchanged, including multicolor placement and background holes;
- only a uniform translation occurs;
- the output bounding-box origin is
  `((canvas_height - bbox_height) // 2, (canvas_width - bbox_width) // 2)`.

Measured input bbox -> target-origin translations were:

- train 0, 6x7 canvas, 2x3 bbox: `(2,1) -> (2,2)`, delta `(0,+1)`;
- train 1, 6x7 canvas, 2x3 bbox: `(4,1) -> (2,2)`, delta `(-2,+1)`;
- train 2, 6x6 canvas, 3x2 bbox: `(3,2) -> (1,2)`, delta `(-2,0)`;
- train 3, 5x5 canvas, 3x2 bbox: `(0,0) -> (1,1)`, delta `(+1,+1)`.

This rules out moving only toward a border, moving one step, centering only one
axis, filling the bbox, recoloring, or normalizing the motif orientation. A
centroid-based interpretation was considered but rejected because the outputs
line up exactly by the rectangular bbox origin while preserving all holes and
cell offsets; bbox centering is the simpler invariant supported by every pair.

For the two public test inputs, the same calculation predicts deltas `(0,-1)`
and `(-1,-2)` respectively.

## Revision 1

Implemented `solve(grid)` by locating all nonzero cells, computing their bbox,
allocating an all-zero canvas of the same shape, and translating every original
nonzero cell by the difference between the floor-centered bbox origin and the
input bbox origin. Empty grids are returned unchanged as a defensive case.

Expected risk: an unseen convention could use ceiling centering when the slack is
odd. The visible 5x5/3x2 example has horizontal slack 3 and places the bbox at
column 1, which selects floor division and directly resolves that ambiguity.

### Check result and stopping decision

The visible-only checker executed successfully and passed all 4/4 training
examples. It intentionally withheld both test-query labels. I made no second
revision because the floor-vs-ceiling ambiguity is already directly witnessed,
all four movement classes shown are handled by the same coordinate rule, and a
second code change would add complexity without new public evidence.
