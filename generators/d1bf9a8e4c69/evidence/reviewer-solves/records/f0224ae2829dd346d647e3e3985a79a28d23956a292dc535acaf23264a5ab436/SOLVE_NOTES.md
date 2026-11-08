# Solve notes

This is a human work log based only on `solve/challenge.json` during the solve phase. I had seen the task's rule earlier while reviewing the generator, so this is not a blind solve; I did not consult the generator, Racket source, reference solutions, private labels, or previous solve explanations after `prepare`.

## Hypothesis 1

Each nonzero 4-connected component is treated as an object. The output clears the object and places its color at the four corners of that object's axis-aligned bounding box.

Evidence from the visible pairs:

- Train pair 1 turns each zigzag/L-like component into a four-dot rectangle.
- Train pair 3 does the same for substantially different shapes and bbox sizes, ruling out a fixed shape template.
- Train pair 2 contains two disconnected color-1 objects. They produce two independent corner sets rather than one global color-1 bounding box, so connectivity—not color alone—defines an object.
- Interior and edge cells that are not bbox corners disappear, while missing bbox corners are added.

## Implementation/probe

Implemented a fresh-grid, same-color 4-neighbor flood fill. For each component, compute min/max row and column and paint the Cartesian product of those extrema. This directly tests the per-component interpretation on all three visible demonstrations and naturally handles repeated colors in separate components.

No deliberately wrong teaching-negative revision was added; the visible demonstrations already disambiguate the strongest plausible per-color rival.
