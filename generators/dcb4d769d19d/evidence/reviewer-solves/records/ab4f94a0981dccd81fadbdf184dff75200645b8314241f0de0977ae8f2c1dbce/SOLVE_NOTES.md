# Solve work log

Earlier exposure: none to this task's generator, rule, private labels, or prior solutions. I read only the visible `challenge.json` after preparation.

## Initial observations

The outputs preserve every non-target region. The changed cells form five-cell orthogonal pluses in color 4. In each training pair, the center of every such plus is a color-2 cell that has no orthogonally adjacent color-2 neighbor in the input. Larger orthogonally connected color-2 components are unchanged. The plus may overwrite a differently colored cell on one arm (for example the 7 and 8 cells in the training examples), so occupancy does not block drawing it.

I checked the hypothesis manually against all four visible pairs:

- pair 1 has four isolated 2-cells and exactly four output pluses;
- pair 2 has two isolated 2-cells and two pluses;
- pair 3 has four isolated 2-cells and four pluses;
- pair 4's isolated 2-cells likewise account for every added 4.

Alternative ideas considered and rejected: copying a colored template, connecting components, or expanding every small red component. Those do not explain why only singleton red components change or why the same plus appears regardless of the other colors.

## Revision 1

Implemented a source-grid scan for color 2 cells with no four-neighbor color-2 adjacency. For each such center, write color 4 to the center and its four orthogonal neighbors, clipping at grid boundaries. Detection uses the original grid so drawing one plus cannot alter later singleton classification.
