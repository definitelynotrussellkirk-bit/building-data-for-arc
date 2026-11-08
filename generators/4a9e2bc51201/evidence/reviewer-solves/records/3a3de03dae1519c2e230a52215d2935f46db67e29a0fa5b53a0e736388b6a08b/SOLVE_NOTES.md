# Fresh visible-example solve notes

## Exposure declaration during reasoning

This is not a blind solve: I reviewed this task's generator and canonical task before
`solve_episode.py prepare`. During this solve I used only `solve/challenge.json`; I
did not reopen the generator, canonical record, Racket source, private labels, or
prior explanation.

## Visible-example hypothesis

Each input has one full-height column of color 5. Treat it as a vertical mirror
guide. For every nonzero, non-5 cell in the original input, compute the same-row
column reflected across that guide. Fill the reflected location only when it is
inside the grid and currently zero. Keep the original mark and the guide.

The examples require both directions: marks may begin on either side. They also
show why this is *empty-target completion*, not unconditional symmetrization. In
the first training pair, some opposing cells are already occupied by different
colors; those colors remain unchanged while only missing partners are added.

## Implementation choice

Scan the original input, write into a deep copy, and test emptiness in the evolving
copy. Since each reflection orbit has only two cells, this matches the demonstrated
preserve-occupied behavior and cannot create a further chain. If no guide is found,
return a copy unchanged as a defensive case outside the shown lesson.
