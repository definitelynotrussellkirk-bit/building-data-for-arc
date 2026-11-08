# Solve work log

## Prior exposure

Before this visible-only solve I had already inspected the selected task's Racket rule while repairing the generator, so this is **not blind**. During this solve I did not reopen the rule, generator, reference solutions, private labels, or earlier solution explanations; I used only the visible examples printed by `prepare`.

## Revision 1

The examples contain two differently colored connected objects. One is an ordinary filled rectangle and remains fixed. The other is a filled rectangular body with a one-cell-wide straight extension aimed at the fixed rectangle. In every output, the extension disappears and the rectangular body is translated in the extension's direction until its nearest edge is flush with the fixed rectangle.

I implemented that literal geometry rather than hard-coding colors, sizes, or directions:

1. Find same-color four-connected components.
2. Select the filled rectangle as the stationary target and the non-rectangular component as the moving creature.
3. Recover the creature's body as its largest completely filled subrectangle; the remaining cells are the tail.
4. Infer travel direction from which side of the body contains tail cells.
5. Compute the distance from the body edge to the target edge, erase the whole creature, and repaint only the body at that translated location.

The two masked queries appear to exercise left-to-right motion: query 0 has a 3x4 body attached to a five-cell left-pointing tail toward an 8x5 rectangle, while query 1 has a 5x3 body and a four-cell right-pointing tail toward a 5x8 rectangle. The generic implementation handles both without query-specific constants.

Remaining uncertainty: the visible support contains exactly one ordinary rectangle and one tailed object, so the solver intentionally assumes that grammar. It does not attempt to choose among multiple rectangular distractors.
