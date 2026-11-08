# Solve work log

## Exposure statement

Before this blind solve I had read only the packet-wide instructions and the
visible episode produced by `solve_episode.py blind prepare`. I did not open the
generator, canonical rule, private labels, reference solution, task notes, or any
prior solve for task `28ba67946524`.

## Observations

Each training input has one large 4-connected multicolor component and one small
detached component. The output keeps selected cells of the large component,
recolors them 8, and erases everything else.

Trimmed large components:

- Example 0 is a 2x5 horizontal stripe. Starting at its left end, the third
  constant-color run is color 4, exactly the output.
- Example 1 is a 2x8 horizontal pattern. Starting at its right end, the third
  run in the upper row is color 9 (the first run is background inside the common
  bounding box), and the third run in the lower row is color 5. Those are exactly
  the output cells.
- Example 2 is a 5x1 vertical stripe. Starting at the lower end, the third run is
  color 3, exactly the output.

In all three examples the detached component has area 2. I therefore interpret
its area as the number of run-boundary crossings, so the selected run is index 2
when runs are numbered from zero. The selected end is the end of the main
component's long axis nearest the detached cue. Runs include background inside
the main component's common bounding box; a selected background run contributes
no output.

## Alternatives considered

I considered shape matching, numeric relationships among ARC colors, nearest
monochrome components, and selecting a fixed third object. Shape and numeric
rules did not consistently explain all three examples. The run-boundary rule
explains every output cell, including the otherwise important leading background
run in example 1. The visible examples do not prove whether multiple detached
components should all act as cues. For the first test, I use the detached
component with the smallest Euclidean cell-to-cell distance to the large pattern;
this treats farther detached bars as distractors. This is the largest remaining
uncertainty.

## Implementation

`solution.py` finds nonzero 4-connected components, chooses the largest as the
pattern and the nearest other component as the cue, then scans rows or columns
along the pattern's longer bounding-box axis. It selects the run after
`area(cue)` boundary crossings from the nearer end and paints nonzero selected
cells 8.
