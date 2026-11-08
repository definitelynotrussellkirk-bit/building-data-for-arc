# Solve work log

## Prior exposure

Before this visible-only solve I had already inspected the assigned generator while repairing it, so I had earlier exposure to the intended rule and its tie behavior.  During this solve I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution notes.  I used only the examples in `WORK/solve/README.md` and the visible-only checker.

## Revision 1

**Hypothesis.** Each isolated nonzero cell is a seed.  Extend its color in a straight line, including the seed, to the nearest grid border.  When several borders are equally near, use the priority top, then bottom, then left, then right.

**Visible evidence.** Ordinary cases establish nearest-border extension.  The centered color 8 in train 3 has equal top/bottom distance and goes upward, establishing top over bottom.  Train 5 contains a top/right tie (color 8) and a bottom/left tie (color 7), selecting top and bottom respectively.  The centered color 9 in train 4 has equal left/right distance and goes left, distinguishing left over right.  Together these examples determine the stated priority among all adjacent tie choices.

**Implementation.** Copy the grid, scan only original nonzero cells, compute the four distances in priority order `(top, bottom, left, right)`, choose the first minimum, and paint from the seed through that border.  Reading seeds only from the original input prevents newly painted cells from being processed as seeds.

**Alternatives considered.** “Extend horizontally or vertically based only on the shorter axis,” “always prefer vertical ties,” and “prefer right on a left/right tie” all fail at least one visible example.  No unexplained visible behavior remains.  I stopped after the first check if it passed all six displayed demonstrations.
