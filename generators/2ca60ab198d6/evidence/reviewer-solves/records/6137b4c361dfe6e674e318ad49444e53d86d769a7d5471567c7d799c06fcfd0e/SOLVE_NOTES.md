# Final visible-only solve notes

## Scope

After preparing this episode I read only `solve/challenge.json`. I did not open
the generator, Racket source, reference solutions, private labels, or earlier
solve notes during the episode. I had already repaired and studied this task, so
`earlier_rule_exposure` is honestly **yes**; this is not a blind solve.

## Hypothesis from the visible examples

Column 0 is a row guide. Keep every row whose guide value is `7`, preserve source
order, and remove column 0 from each retained row.

The demonstrations rule out the strongest alternatives:

- examples 3 and 4 retain four rows, so retention is not capped at three;
- examples 2 and 4 contain rejected nonzero guide cells, so “keep nonzero” is
  wrong;
- examples 3 and 4 include adjacent selected rows, so rows do not alternate;
- color 7 occurs in payload cells on both kept and rejected rows, so only the
  guide position controls selection.

The direct filter-and-crop implementation passed all four visible examples on
its first revision. I stopped rather than manufacture extra attempts.
