# Post-repair solve notes

This is a human-readable work log from the visible examples. I had earlier rule exposure while reviewing this generator, so this is not a blind inference record; I did not consult the generator, Racket source, reference solutions, or private labels after preparing this episode.

## Visible-example hypothesis

Each changed cell is the unique zero corner of a 2×2 window whose other three cells all have the same nonzero color. Complete every such local window independently, including multiple windows of the same color that touch and form one larger connected component. Preserve all other cells.

The examples distinguish this from an isolated-object shortcut: train example 1 contains two touching same-color L windows in one connected six-cell shape, and both missing outer corners are filled. Train example 2 likewise contains a connected same-color pair of windows plus two isolated windows.

## Implementation choice

Scan all 2×2 windows in the original input, not an incrementally modified grid. A window qualifies only when it contains exactly one zero and exactly three copies of one nonzero color. Write all qualifying missing corners into a copied output. Reading from the original prevents a newly filled corner from recursively creating an unintended second-generation match.

## Predicted queries

- Query 0: fill the upper-left missing corner of the color-6 L and the upper-right missing corner of the color-8 L.
- Query 1: fill both outer missing corners of the connected color-4 shape, plus one missing corner for color 1 and one for color 9.
