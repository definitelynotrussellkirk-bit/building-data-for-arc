# Post-repair visible-example solve log

This is an exposed solve: I previously inspected the repaired task while reviewing it, but during this episode I used only `solve/challenge.json` and did not reopen the generator, Racket rule, reference solutions, or private labels.

## Revision 1 hypothesis

Each input contains:

- one 4-connected color-1 component that serves as a literal shape template;
- one or more 4-connected color-3 candidate components;
- isolated singleton marker cells in other colors, with one color occurring strictly most often.

The output starts as an all-zero grid. A color-3 candidate is copied at its original coordinates and recolored to the marker majority color iff its normalized coordinate set exactly equals the color-1 template's normalized coordinate set. Orientation is literal: the examples distinguish an exact translated copy from equal-area and differently shaped candidates. The template, markers, and nonmatching candidates disappear.

Visible evidence:

1. Train 1 selects the upper four-cell zigzag, not the lower equal-size T; marker color 5 occurs twice versus one 9.
2. Train 2 selects both translated zigzags and excludes the T; marker color 2 occurs three times.
3. Train 3 selects the translated horizontal zigzag and excludes the square and two-cell object; marker color 9 occurs twice.

Rejected rivals: recolor every green object; choose equal cell count only; choose the numerically largest marker; keep only the first match. Each is contradicted by at least one visible example.

## Check result and stop

Revision 1 executed successfully and matched all 3/3 visible training outputs. No visible evidence motivates a second revision; the rule explains selection, recoloring, deletion, multiplicity, and marker choice simultaneously.
