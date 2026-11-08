# Solve work log

## Exposure record

Before this post-repair episode I had already inspected the task's rule and generator while repairing it, so earlier rule exposure is **yes**. During this episode I kept the generator, Racket rule, private labels, reference solutions, and the earlier blind-solve notes closed. I used only `solve/challenge.json` plus the solve harness files.

## Revision 1 hypothesis

The unique border cell of color 4 is a light/direction marker and is removed in the output. Every other nonzero cell is a caster. Each caster emits a color-4 ray in the direction away from the light until the opposite grid boundary; after all rays are drawn, the original caster colors are restored on top.

The visible examples determine direction and corner precedence:

- light on the left edge -> cast right;
- light on the right edge -> cast left;
- otherwise light on the top -> cast down;
- otherwise light on the bottom -> cast up.

The bottom-right and bottom-left training examples are important: both cast horizontally, so side-edge membership has priority at corners rather than bottom-edge membership.

I implemented this directly, with validation for one rectangular grid and exactly one border light. I deliberately did not use a shortcut such as keeping only the farthest caster on a row/column: the visible outputs fill gaps between multiple casters and restore all caster cells.

Remaining uncertainty before checking: none about the visible transformation; private query labels remain unavailable by design.
