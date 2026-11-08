# Exposed solve work log

This is a human-readable reasoning log written from the visible examples in `README.md`. I had already seen the intended rule during generator repair, so this solve is **not blind**; I did not reopen the generator, Racket source, reference solutions, prior solve notes, or private labels during this episode.

## Visible-example inference

Across all three demonstrations, the only changed objects are isolated gray components consisting of exactly two horizontally adjacent cells. They become cyan (8).

The following remain gray (5):

- a two-cell vertical component, so “recolor every size-two object” is too broad;
- a horizontal length-three or length-four component, so “recolor every object containing a horizontal pair” is too broad;
- a 2x2 square, so the decision applies to the whole 4-connected object, not merely local adjacent pairs.

Hypothesis: find 4-connected gray components; recolor a component iff its normalized shape is exactly `[(0,0), (0,1)]`. Preserve all other cells and the input dimensions.

## Implementation choice

The solution explicitly traverses 4-connected gray components and checks exact component size and orientation. This avoids accidentally recoloring a pair embedded inside a longer run or square. No alternative revision was needed because this rule explains every visible input/output pair without exceptions.
