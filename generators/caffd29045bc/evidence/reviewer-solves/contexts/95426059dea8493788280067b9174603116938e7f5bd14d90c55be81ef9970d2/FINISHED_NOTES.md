# Visible-only solve notes — caffd29045bc

The examples contain a unique full vertical color-9 column. Every colored cell other than 0 and 9 is retained and copied to the same row at equal horizontal distance on the opposite side of that guide.

The demonstrations rule out a fixed left-to-right rule: example 1 starts on the right. Example 2 also shows disconnected source pieces and cells immediately next to the guide, so the operation applies independently to every colored source cell rather than only one component or only cells behind a blank gap.

Implementation: locate the unique all-9 column, deep-copy the grid, and for every original non-{0,9} cell write its color at column `2*axis-c` when in bounds. I did not consult the Racket rule during this solve, but I had necessarily seen the task semantics earlier while repairing the generator, so this is not blind.
