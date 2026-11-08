# Solve work log

## Exposure and observations

I had not opened this task's generator, Racket rule, private labels, reference
solution, notes, or audit evidence. I used only the visible examples printed by
`python3 review.py blind prepare` and the public challenge files.

The bottom row contains red (2) seeds. In every example, each seed launches a
vertical red path upward. A path continues in its current column until the next
cell is a gray (5) blocker. The blocker is preserved; at the row immediately
below it, the path takes one horizontal step right, then continues upward in the
new column. Gray cells that are not on a path are unchanged. Straight paths and
right-turning paths can coexist.

Examples supporting this:

- Example 1: the path from bottom column 7 rises to row 3, encounters gray at
  `(2, 7)`, adds the connector `(3, 8)`, and continues in column 8.
- Example 3: blockers on paths from columns 1 and 11 independently shift those
  paths to columns 2 and 12, while the path from column 6 stays straight.
- Gray cells at columns never reached by a path remain inert, ruling out a rule
  that reacts to every gray cell globally.

## Revision 1

Hypothesis: copy the grid; for each red cell in the bottom row, scan upward.
When the original input has gray at the current path column, move the path one
column right, paint the horizontal connector in the row below, and continue.
Otherwise paint the current cell red. The visible examples do not show a blocker
at the right edge; I stop rather than invent a left turn or wraparound there.

A local assertion against the first visible training pair failed before this
revision because the provided skeleton raised `NotImplementedError`. After
implementing the rule, I tested all visible training pairs and then used the
packet's visible-only checker.

Remaining uncertainty: the examples do not establish behavior for a gray blocker
in the rightmost column or for blockers arranged so that two paths collide. The
queries appear to remain within the demonstrated right-turn regime.
