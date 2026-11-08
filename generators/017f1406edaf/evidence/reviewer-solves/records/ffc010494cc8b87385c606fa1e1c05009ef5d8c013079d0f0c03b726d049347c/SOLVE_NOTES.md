# Solve work log

## Exposure declaration before solving

This is the required post-repair, exposed solve. Before preparation I had read and repaired this task's generator and had read its canonical rule, so I already knew the intended transformation. During this solve episode I did **not** reopen the generator, Racket rule, reference solutions, private labels, or earlier solution explanations. I used only the visible presentation produced by `solve_episode.py prepare` and my own Python.

## Revision 1 — top-row count selects an eligible component

Visible evidence:

- Training 0 has five blue (`1`) cells in row 0 and selects the five-cell color-2 component.
- Training 2 has four blue cells in row 0 and selects the four-cell color-2 component.
- Training 1 is the important exclusion case: row 0 has five blue cells, while additional blue cells occur lower in the grid. The selected nonblue component still has area five, so only row-0 blue cells are counted.
- Training 3 is the other exclusion case: a three-cell color-2 object touches row 0 and is not selected; the separate three-cell color-6 object is selected. Thus candidate objects touching row 0 are excluded, as are blue objects.
- Every output is a blank grid of the original shape with only the selected component recolored cyan (`8`).

Hypothesis implemented: count blue cells in row 0; enumerate nonzero monochrome 4-connected components in row-major order; ignore blue components and every component touching row 0; select the first remaining component with matching area; erase everything else and paint that component `8`.

Query sanity checks from visible inputs:

- Query 0 has six top-row blue cells. Its six-cell color-3 object is selected; the color-2 and color-4 objects have five and four cells.
- Query 1 has four top-row blue cells. The four-cell color-2 column touches row 0 and the lower blue cells are excluded, leaving the lower four-cell color-8 object as the selected candidate.

Remaining uncertainty is limited to behavior outside the displayed domain (for example no eligible match or multiple eligible matches). The examples support row-major first-match behavior; the implementation leaves a blank output when no match exists and stops at the first match.
