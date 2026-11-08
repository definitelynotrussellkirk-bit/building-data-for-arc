# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator before this solve episode, so earlier rule exposure is **yes**. During this episode I used only the visible examples in `README.md`; I did not reopen the generator, canonical rule, reference solutions, or private labels.

## Revision 1

All three demonstrations preserve every nonzero cell and replace only zeros. The completed grids repeat a small two-dimensional tile: examples 0 and 2 use a 2-row by 3-column tile, while example 1 uses a 3-row by 2-column tile. A row-only rule is insufficient for example 0/2 because the damaged row hides most horizontal residues; a column-only rule is insufficient for example 1 because the damaged column hides most vertical residues.

Hypothesis: find the smallest row/column period for which every visible nonzero cell at the same modular offset has one consistent color, reconstruct that tile from all visible cells, and fill each zero from its modular offset. I search candidate periods 1 through 5 in row-major order, matching the scale visible in the examples. Remaining uncertainty is only whether an unseen query uses a larger period; the two visible query shapes and demonstrations make that unlikely.
