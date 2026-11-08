# Solve notes — 54628ce9692d

Earlier rule exposure: **yes** (this solve follows the generator repair), so this is a visible-only replay rather than a blind inference claim. I did not reopen or consult the Racket/reference solution while authoring this solve.

## Hypothesis

The modal colour is background. Each separated non-background component is a rigid colour-1 object whose other colours are boundary connectors. Repeated connector colours pair two objects. Translate, but do not rotate, the objects so equal-colour connector cells are cardinally adjacent and their boundary normals face each other; an unpaired connector is a free endpoint. Crop the assembled cells to their bounding rectangle.

## Implementation probe

1. Extract 4-connected non-background components.
2. Jointly infer opposite outward directions for each repeated connector pair, strongly preferring the component bounding-box side occupied by the marker and using local object mass as a tie-breaker.
3. Convert each pair into a translation constraint and solve the connector graph by breadth-first traversal.
4. Paint all translated cells on the modal background and crop.

The demonstrations show no rotation, no recolouring, and no overlap. A disconnected connector graph is outside the apparent task distribution; the implementation has only a conservative fallback for it.
