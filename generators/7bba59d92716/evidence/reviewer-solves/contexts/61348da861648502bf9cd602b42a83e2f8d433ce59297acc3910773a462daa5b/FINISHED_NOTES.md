# Visible-only solve notes

I had already reviewed the task's generator and authority before this episode, so this is **not blind**; earlier rule exposure is `yes`. During this solve I used only the newly prepared visible examples and did not reopen the generator, Racket rule, canonical source, prior solution, or private labels.

Across the three demonstrations, output differs only by changing selected color-1 cells to color 2. The selected cell is the middle of a four-connected color-1 component that is a straight vertical line of exactly five cells. Vertical runs embedded in a larger branched component are unchanged, as are length-3/4/6 vertical lines and horizontal length-5 lines.

Implementation plan: enumerate four-connected color-1 components. A component qualifies only when it has five cells, all in one column, and its rows are five consecutive integers. Recolor the third row of each qualifying component to 2; copy every other cell unchanged.
