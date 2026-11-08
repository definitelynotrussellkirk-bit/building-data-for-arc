# Solve work log

## Exposure declaration

I had already inspected this task's generator and canonical rule while repairing it, so this is an exposed post-repair solve. During this solve episode I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations; I used only the freshly prepared visible examples.

## Revision 1 hypothesis

The gray cells form chamber walls. A gray connected component is active only when the entire component is exactly one rectangular border. This explains training example 1: the two upper visible rectangles touch, merge into one non-rectangular gray component, and their blue/red markers remain unchanged; the separate lower rectangle transforms.

Inside each active rectangular chamber, color 1 becomes an orange (7) vertical line and color 2 becomes an orange horizontal line. The ray extends in both directions through interior zero cells, stops before yellow (4) blockers, and also stops at the gray wall. The seed itself becomes 7. Yellow blockers and all inactive chambers remain unchanged.

The implementation therefore finds 4-connected gray components, accepts only components equal to the border of their bounding box, and traces the appropriate rays using the unmodified input as the collision map. This should handle both isolated chambers in examples 0 and 2 and reject the touching pair in example 1.

Remaining uncertainty: the visible examples contain one seed per visible rectangle, so interactions between multiple seeds in a single active chamber are untested. The implementation processes all such seeds independently without treating one seed as a blocker.
