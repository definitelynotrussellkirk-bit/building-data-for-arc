# Solve notes

This is a human work log based only on `solve/challenge.json`. I had earlier
rule exposure because I repaired this task's generator before this required
post-repair solve; I did not consult the generator, Racket source, private
labels, or reference solutions while writing this solve.

## Visible-pattern inference

Each input has two equal-width panels separated by a full vertical column of
9s. The output has the height and width of one panel. Across all four visible
training pairs:

- an output cell is 8 when the aligned cells in both panels are nonzero;
- it is 0 when either aligned panel cell is 0;
- the original nonzero colors do not matter, including the equal-color example;
- the divider itself is removed.

So the transformation is the binary support intersection of the two panels,
rendered in color 8.

## Implementation

Find the divider in the first row, validate equal panel widths and the full
vertical divider, then zip the aligned cells row by row. Emit 8 for a pair of
nonzero values and 0 otherwise.

No intentional negative or diagnostic solution revision was constructed; the
first implementation directly expresses the rule supported by every visible
example.
