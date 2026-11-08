# Solve work log

## Exposure record

I had already read the task rule and generator while repairing the assigned generator, so this is an exposed post-repair solve, not a blind solve. During this solve I did not reopen the generator, Racket source, reference solution, private labels, or the earlier blind-solve notes. I used only the visible examples produced by `solve_episode.py prepare`.

## Revision 1

**Observation.** Every nonzero color appears twice. In example 0, the two color-4 cells are opposite corners of the output's hollow rectangle. Example 1 applies the same operation independently to colors 7 and 9, including nested rectangles. Example 2 is important because each pair has the opposite diagonal direction from example 0, yet the output is still the full bounding-box border.

**Hypothesis.** Group nonzero cells by color. For every color with exactly two cells, compute the minimum and maximum row and column and draw the four sides of that bounding rectangle on a fresh zero grid. Pair direction and color value are irrelevant; colors are processed independently.

**Implementation.** `solve/solution.py` collects positions by color, allocates a same-size zero grid, and paints both extreme rows and both extreme columns for each two-cell group.

**Alternatives rejected.** Connecting the two points with an L path fails all examples because the opposite sides are also drawn. Filling the whole bounding box fails because interiors remain zero. Handling only positive-slope pairs fails example 1 and example 2, which contain negative-slope pairs.

**Remaining uncertainty.** The visible examples establish behavior for one or two colors, diagonal corner pairs, nested rectangles, and both diagonal slopes. They do not show malformed groups, so the implementation conservatively ignores colors that do not occur exactly twice rather than inventing a rule for them.
