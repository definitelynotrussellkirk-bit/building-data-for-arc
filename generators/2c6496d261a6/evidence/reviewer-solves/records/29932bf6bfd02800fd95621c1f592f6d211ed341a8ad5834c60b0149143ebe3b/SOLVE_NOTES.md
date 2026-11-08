# Exposed post-repair solve: 2c6496d261a6

## Exposure declaration

I previously read the rule and generator while repairing this task. This is an
exposed, rule-informed solve, not a blind result. Since preparing this episode,
I have read only its public challenge, not the generator, Racket rule, reference
solutions, earlier solution explanations, or private labels. The checker alone
will execute the program and report visible examples.

## Visible evidence and first hypothesis

The transformation preserves the grid shape and keeps each color only when all
its occurrences occupy one row. In demonstration 1, color 1 has six occurrences
in a single row and survives, while color 2 has six occurrences spread across
rows and disappears. Its singleton color 8 survives. Demonstration 2 likewise
keeps five copies of color 5 in one row and erases five copies of color 6 across
several rows, even though two copies of color 6 are adjacent in one row.
Demonstration 3 retains horizontal color 9 plus singleton colors 7 and 6, while
removing color 3 throughout the grid.

These observations rule out total frequency as the decision criterion and show
why a local horizontal repeat alone cannot authorize retention. I did not submit
an intentional wrong program or invent an earlier failed attempt.

## First program

One pass builds a set of occupied row indices for each nonzero color. A second
pass copies the original value only for colors with a row-set of size one, and
writes zero otherwise. It uses no fixed color labels, row positions, dimensions,
lookup table, or query labels.
