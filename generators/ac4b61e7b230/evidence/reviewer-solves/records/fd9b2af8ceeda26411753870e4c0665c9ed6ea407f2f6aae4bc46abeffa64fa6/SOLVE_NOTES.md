# Solve work log

Earlier exposure: none. Before this solve I had read only the packet-level instructions and the assignment text; I did not open this task's generator, rule, notes, solutions, audit records, or private labels.

## Revision 1 — compass slide until the next step collides

The three visible examples contain one red (`2`) object and one azure (`8`) object. The azure object stays fixed. The red object keeps its exact shape and moves toward the azure object:

- when their row ranges overlap, it moves horizontally;
- when their column ranges overlap, it moves vertically;
- it stops at the last position before a one-cell continuation would overlap an azure cell.

This also explains the third example's exact six-row translation: a seventh row would overlap the azure square at one occupied cell. I generalized the direction independently on each axis from the two bounding boxes. Thus a diagonally separated pair moves in one of the four diagonal compass directions. For the second query, this predicts four down-left steps; the fifth would collide.

Probe: ran the candidate directly against all three visible training pairs before invoking the packet checker. All three outputs matched exactly.

Remaining uncertainty: the visible demonstrations do not directly show diagonal motion, so the second query tests that generalization. A rival could choose a two-stage cardinal path or re-center the shapes, but neither is supported by the constant one-step translation process that exactly explains all observed stopping positions.
