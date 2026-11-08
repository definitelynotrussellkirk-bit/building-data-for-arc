# Solve work log

## Exposure statement

Before this solve I had not opened the generator, canonical rule, reference solution,
private query labels, audit records, or any task-specific earlier explanation for
`0e71518de287`. I used only the visible grids printed by `blind prepare` and the
public `challenge.json`.

## Revision 1 — marker selects a hollow rectangle

**Hypothesis.** Every input contains two hollow rectangles outlined in color 4 and
one singleton marker of another color. The marker sits immediately outside one
rectangle, aligned with one of its sides. The output preserves everything and fills
the selected rectangle's zero-valued interior with the marker color.

**Visible evidence.** In the four demonstrations, markers above, below, left, and
right of a rectangle respectively select that rectangle. Interior sizes vary from
`1×2` through `3×3`; the unmarked rectangle is unchanged. Thus selection should be
geometric rather than tied to orientation, size, position, or marker color.

**Probe.** I first ran an automated assertion over all visible training pairs while
`solution.py` still raised `NotImplementedError`; it failed as expected. I then
implemented orthogonal color-4 component extraction, validated complete rectangular
borders, selected the rectangle with minimum marker-to-bounding-box distance, and
filled only zero cells strictly inside its border.

**Alternatives rejected.** Filling the largest rectangle fails demonstrations where
the marker chooses the smaller one. Choosing by fixed direction or color also fails
because all four directions and several marker colors occur.

**Remaining uncertainty.** The visible data always has a complete color-4 border and
a single external marker. The implementation safely leaves the grid unchanged if
those conditions are absent, but that fallback is not established by examples.
