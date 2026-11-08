# Solve work log

## Prior exposure

I had not opened this task's generator, canonical rule, reference solutions,
private labels, or audit evidence. I used only the visible presentation produced
by `python3 review.py blind prepare` and `WORK/solve-blind/challenge.json`.

## Hypothesis development

The output always preserves every object except one 4-connected blue (`1`)
component, which is recolored red (`2`). Each grid also contains exactly two
other colors. I first considered proximity, shape matching, and pairing the
colored objects with nearby blue objects. Those explanations were inconsistent:
for example, in training example 2 the chosen blue object is not the closest one
to the higher-colored cue.

A consistent geometric explanation is that the two cue colors form a direction.
For each training grid, take the centroid vector from the lower color id to the
higher color id, project every blue component centroid onto that vector, and
select the maximum projection:

- example 0: cue `5 -> 6` points down/right; the southeast-most projected blue
  component is recolored;
- example 1: cue `8 -> 9` points mostly upward; the uppermost projected blue
  component is recolored;
- example 2: cue `4 -> 7` points mostly left; the left/up extreme is recolored.

A secondary probe compared all ordered pairs of blue centroids with the cue
vector. The destination of the best-aligned pair also matched every training
answer, but that rule is less stable: it can prefer a short nearly-parallel pair
instead of the globally extreme object. The maximum-projection interpretation is
simpler and directly matches an arrow selecting an extreme object.

## Implementation

`solution.py` finds 4-connected blue components, computes cue and component
centroids, selects the component with maximum dot product against the cue vector,
and recolors it `2`. It returns the input unchanged for malformed cases rather
than raising.

## Remaining uncertainty

The visible examples consistently make the lower numeric cue color the tail and
the higher numeric cue color the head. This may be a generator convention rather
than a universal ARC color-order convention. The two test grids retain the same
pattern (`3 -> 9` and `4 -> 6`).
