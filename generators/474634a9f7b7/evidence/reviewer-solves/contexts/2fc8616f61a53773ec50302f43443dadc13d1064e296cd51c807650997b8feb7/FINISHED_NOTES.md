# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
reference solution, audit evidence, or prior solve notes.  I used only the visible
examples produced by `review.py blind prepare` and local analysis of
`challenge.json`.

## Hypothesis

Every example contains four differently colored connected objects around the
canvas center.  Total non-background area is conserved.  Exactly one object—the
one with the greatest area—gains three cells, while each of the other three loses
one cell.  For every losing object, the deleted cell is the unique colored cell
with minimum squared distance to the canvas center.

The three received cells form a straight bar at the winner's outward-facing end.
The placement observed in the four training examples covers all four winner
quadrants:

- upper-left winner: vertical bar immediately left, aligned with its lower edge;
- upper-right winner: horizontal bar immediately above, aligned with its left edge;
- lower-left winner: horizontal bar immediately below, aligned with its right edge;
- lower-right winner: vertical bar immediately right, aligned with its upper edge.

This gives the interpretation “the largest object takes one unit from each other
object.”  The exact interior shapes vary, but the nearest-center deletion and the
quadrant-specific three-cell continuation are invariant.

## Probe and implementation

I enumerated per-color cell counts and input/output set differences for all four
visible examples.  The changes were always `+3, -1, -1, -1`; all twelve deleted
cells were the unique closest cells to the board center.  Each winner quadrant
occurred once, allowing the four outward continuation cases to be read directly.

`solution.py` finds the modal background color, groups all non-background cells by
color, removes the closest-to-center cell from each non-winner, classifies the
winner by centroid quadrant, and adds the corresponding three-cell bar.

## Remaining uncertainty

The visible data do not show tied object sizes, a closest-cell tie, or a winner
near a boundary.  The generated examples leave enough margin, and the query count
profiles have unique winners, so the implementation keeps the observed simple
contract rather than inventing tie behavior.
