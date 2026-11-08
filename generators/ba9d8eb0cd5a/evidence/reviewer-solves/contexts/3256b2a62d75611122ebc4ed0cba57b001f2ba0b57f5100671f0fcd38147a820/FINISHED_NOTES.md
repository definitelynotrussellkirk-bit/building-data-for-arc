# Visible-example solve log

## Revision 1 — stable row-wise left compaction

Across all three visible training pairs, each row is transformed independently.
Zeros are removed, the nonzero values stay in their original left-to-right order,
and enough zeros are appended to restore the original row width. Empty rows stay
empty. Evidence against sorting is visible in rows such as `9,1,4` and
`7,2,8,8,8`, whose order is unchanged in the output.

Implementation: collect `value != 0` per row, then right-pad with zeroes. The
shape is preserved exactly and no color values are changed.

Exposure note: this is a post-repair solve, so I had already seen the assigned
rule during generator review. During this solve episode I consulted only
`solve/challenge.json`, not the generator, Racket source, reference solution, or
private labels.
