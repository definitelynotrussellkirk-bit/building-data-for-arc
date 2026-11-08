# Solve work log

## Exposure statement

Before this post-repair solve I had already inspected the canonical task rule and
the generator while performing the assigned repair. I therefore record earlier
rule exposure as **yes**. During this solve I did not reopen the generator,
Racket rule, reference solution, private labels, or earlier task-specific solve
notes; I used only the visible examples in `challenge.json` and the visible-only
checker.

## Revision 1

The visible examples split the blue objects into three recurring shapes:
vertical lines of length three, vertical lines of length four, and horizontal
lines of length three. Across all three training pairs, exactly the vertical
length-three components change from blue 1 to red 2. The horizontal triples and
vertical length-four components remain blue. This rules out both “recolor all
three-cell objects” and “recolor every vertical object.”

I implemented a 4-connected component scan over color 1, normalized each
component by its top-left coordinate, and recolored a component only when its
normalized cells are `[(0,0), (1,0), (2,0)]`. The transformation preserves the
canvas and all non-target cells.

Remaining uncertainty before checking: none material from the visible examples;
the length-four negatives explicitly establish that exact length matters.
