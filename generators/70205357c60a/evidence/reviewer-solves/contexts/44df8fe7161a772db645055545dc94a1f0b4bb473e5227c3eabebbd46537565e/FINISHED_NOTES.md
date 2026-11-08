# Solve notes

## Visible-example hypothesis

The output keeps the grid shape, all background `0`s, and every `5` that is not
surrounded on all four cardinal sides. A `5` changes to `2` exactly when the
cells immediately above, below, left, and right are all `5` in the original
input.

This explains the solid blocks in example 0: only their non-boundary interiors
turn to `2`. It also explains the notches in examples 1 and 2: cells geometrically
inside a component's bounding box remain `5` when a notch removes even one
required cardinal neighbor. The test inputs contain the same solid/notched
patterns, so a simultaneous local pass over the original grid should apply.

I implemented one immutable-input pass and did not use diagonal neighbors,
component bounding boxes, or iterative propagation.
