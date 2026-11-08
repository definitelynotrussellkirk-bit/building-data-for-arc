# Solve work log

I had not opened the task generator, Racket rule, task notes, private labels, or
any earlier solution explanation before this solve.  I used only the public
challenge printed by `blind prepare`.

## Revision 1 — baseline red test

The untouched template raised `NotImplementedError`; the provided visible-only
check therefore reported an execution error on all three visible examples.  I
kept that attempt as the required failing baseline.

## Revision 2 — shape-key hypothesis

Observation: every nonzero color other than blue (`1`) is a singleton marker a
small distance to the right of one blue connected component.  That nearby blue
component remains blue in the output.  All *other* blue components with the
same shape and orientation are recolored to the marker's color.  Translation
is irrelevant; rotation and reflection are not applied.

Examples supporting the rule:

- In training example 0, the marker `9` names the three-cell L with its lone
  upper cell on the right; both distant copies become `9`, while the nearby
  exemplar stays blue.
- The `4` marker in that example names a horizontal length-three bar, and the
  distant bar becomes `4`.
- Training examples 1 and 2 repeat the same relation for tetrominoes and
  five-cell shapes, including multiple distant copies.

Implementation plan: find 4-connected blue components; normalize each component
by its minimum row/column; associate each singleton marker with the blue
component of minimum Manhattan distance; leave those reference components
unchanged; recolor every non-reference component with a matching normalized
shape.  The two query grids contain exact translated matches for each labelled
reference shape, including two `9` targets in query 0.

Remaining uncertainty: association by nearest Manhattan distance assumes the
visually adjacent component is unique, as it is in every visible example.
