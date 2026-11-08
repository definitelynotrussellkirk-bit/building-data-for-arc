# Solve work log

## Exposure disclosure

Before this source-closed solve I had already reviewed and repaired this task's generator, so I had earlier exposure to the transformation family. During this solve I did **not** reopen the generator, the Racket rule, reference solutions, private query labels, or earlier solution notes. I used only the visible grids in `solve/README.md` / `challenge.json`.

## Revision 1 — complete each domino into a 2×2 square

### Observation

Every nonzero object in the four training inputs is an isolated, monochromatic two-cell domino. The outputs retain those two cells and add exactly two cells of the same color:

- a horizontal domino gains an identical row directly **below** it;
- a vertical domino gains an identical column directly **to its right**.

This makes each object a solid 2×2 square. Colors, canvas dimensions, object positions, and all background cells are otherwise unchanged. The four examples jointly include both orientations, several colors, two and three objects, and edge-adjacent legal placements.

### Alternatives considered

- Always copy downward: contradicted by every vertical example.
- Always copy rightward: contradicted by every horizontal example.
- Use a fixed output color: contradicted by the preserved object colors.
- Transform only the first object: contradicted by examples containing two or three completed objects.
- Complete the square on whichever side has room: unnecessary and contradicted by the consistent down/right convention; all visible objects have room in the required direction.

### Implementation

`solution.py` finds 4-connected nonzero components, leaves unrelated non-domino components unchanged, and for each valid two-cell domino writes the two missing cells in the down/right 2×2 completion. This component-based implementation handles multiple objects and does not depend on particular colors or dimensions.

### Remaining uncertainty

The visible examples leave essentially one convention-specific uncertainty: a malformed horizontal domino on the last row or vertical domino in the last column could not be completed down/right. No training or query object has that form; the solver conservatively leaves such a component unchanged rather than wrapping or overwriting elsewhere.
