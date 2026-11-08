# Solve notes

This is a human work log from the visible examples only. I had earlier rule exposure from reviewing the assigned generator, so this is not a blind solve; I did not reopen the generator, Racket rule, reference solutions, or private labels during this solve.

## Hypothesis

- Color 7 is background.
- Segment color-6 cells into maximal **orthogonally connected** components.
- A non-6/non-7 cell orthogonally adjacent to a component is its label.
- Replace every cell of a labeled component by that label color.
- Leave an unlabeled component as color 6.
- Erase all label/marker cells to background 7.

The visible examples support component-local recoloring, including diagonal-near components that remain separate. I used a deterministic minimum only as defensive behavior if an unseen malformed component has multiple label colors; the visible inputs show at most one.
