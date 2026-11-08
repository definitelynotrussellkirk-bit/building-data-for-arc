# Solve notes

This is a human-visible-example work log. I did not reopen the generator, Racket rule, reference solutions, or private labels during this solve phase. I had earlier rule exposure from the required generator-review work and will declare that at finish.

## Hypothesis

The output preserves shape and every existing nonzero cell. A zero cell is filled only when its four orthogonal neighbors (up, down, left, right) are all the same nonzero color. Diagonal agreement is irrelevant. An already occupied center stays unchanged even if its four arms agree.

Evidence from the demonstrations:

- Training example 0 fills the two hollow cardinal-plus centers.
- Training example 1 leaves the occupied center at row 1, column 1 unchanged despite four matching color-3 arms; it fills only the two hollow centers.
- Training examples 1 and 2 leave diagonal, partial-arm, and mixed-arm patterns unchanged.

The implementation scans the original input, writes qualifying centers into a copy, and therefore cannot let a newly filled cell trigger another fill during the same pass.
