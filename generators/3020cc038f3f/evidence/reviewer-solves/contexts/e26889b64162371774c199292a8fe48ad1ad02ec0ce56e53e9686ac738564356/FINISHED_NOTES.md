# Post-repair solve notes — 3020cc038f3f

Earlier exposure: **yes**. I reviewed and repaired this task before this episode, so this is not a blind solve. During the episode I consulted only `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solutions, private labels, or earlier explanations.

## Hypothesis

Each colored object is cropped to its own bounding box and translated to a common top-left origin. The value at `(0,0)` selects a Boolean set operation on the two normalized occupancy masks, and selected cells are painted 8 on a canvas whose dimensions are the maximum operand bounding-box dimensions.

Visible evidence:

- Both control-5 demonstrations retain only cells occupied by both normalized shapes, so 5 is intersection.
- The control-3 demonstration contains every occupied normalized cell from either shape, so 3 is union.
- The natural remaining operation for control 4 is symmetric difference (XOR); it is implemented even though this generated lesson does not visibly exercise it.
- The examples preserve the full maximum operand bounding box rather than tightly cropping the result.
- For an empty result, a 1x1 zero grid is the least ambiguous representable output and matches the task family convention remembered from earlier exposure; this edge case is not needed by the visible test inputs.

## Implementation

Extract colors 1 and 2, independently normalize each by its minimum row and column, apply union/XOR/intersection according to control 3/4/5, and paint the result with 8. No input mutation or reference lookup is used.
