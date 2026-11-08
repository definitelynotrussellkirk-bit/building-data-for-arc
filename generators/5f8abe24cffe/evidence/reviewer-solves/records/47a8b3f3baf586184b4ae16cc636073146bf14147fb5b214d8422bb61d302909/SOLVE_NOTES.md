# Blind solve notes — 5f8abe24cffe

## Visible-pattern hypothesis

The input contains three separate rectangular frames made of color 1. After
removing each frame and trimming exterior zero padding, the first two interiors
form an analogy: the second is a rotation/reflection of the first. The required
output is the same dihedral transformation applied to the third interior.

Visible checks:

- Example 1: the first tight pattern is flipped top-to-bottom to obtain the
  second; flipping the third top-to-bottom gives the 2×2 output.
- Example 2: the same top-to-bottom flip maps the first to the second and maps
  the third to the output.
- Example 3: a left-to-right flip maps the first to the second and maps the
  third to the output.

## Implementation

Detect 4-connected color-1 components whose bounding-box perimeter is a complete
rectangle, order the frames in reading order, crop their interiors tightly around
nonzero cells, identify the matching member of the eight square-grid dihedral
transforms from frame 1 to frame 2, and apply it to frame 3.

No generator, canonical rule, private labels, prior solution, or task notes were
consulted. This is the first implementation attempt.

## Pre-check implementation refinement

A local visible-example run passed all three examples. Before creating the first
recorded checker revision, I replaced transform-list index reuse with named
transforms so source symmetries cannot misalign deduplicated source/query lists.
This did not change the inferred rule or any visible output.
