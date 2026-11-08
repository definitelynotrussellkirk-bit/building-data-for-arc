# Visible-only solve log

I read only the public challenge for task 22398bb29643. I had not opened this
task's generator, rule, notes, solutions or audits, or the assigned repair
generator. Initial archive inspection exposed unrelated historical tooling
README files; none described this target. No reference was consulted here.

The output contains one color for each separated object. Example 1 has two
separated red objects and two red output cells, ruling out a list of distinct
colors. Object area does not determine the order: example 0 has areas 3, 5,
3, 3, 4 in its output order. Reading objects by their topmost occupied cell
in row-major order explains all three demonstrations.

Revision 1: detect monochrome four-connected nonzero components by a flood
fill initiated in row-major order, then emit their colors as one output row.
The visible examples do not distinguish four-connectivity from eight-connectivity
or all possible rules for heavily overlapping vertical object extents. I choose
the simplest observed reading order without consulting hidden labels.

Query expectations from this hypothesis are [2, 2, 9] and [5, 2, 6]. These are
predictions, not scored answers. The public checker will establish only visible
fit and executable query outputs. No deliberate failed attempts were created.
