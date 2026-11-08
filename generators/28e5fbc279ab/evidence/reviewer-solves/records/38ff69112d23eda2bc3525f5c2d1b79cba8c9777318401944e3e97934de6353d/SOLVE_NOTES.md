# Solve work log

This is a human-visible-example work log, not a captured model trace. I had
already reviewed this task's generator/rule family before the episode, so this is
an exposed solve (`earlier-exposure yes`). During this solve I consulted only
`solve/challenge.json` and my own Python files; I did not reopen the Racket rule,
generator, private labels, reference solutions, or earlier solution explanations.

## Hypothesis 1

The output preserves the input and copies a connected green (`3`) template at
each singleton of another color, using that singleton's color. The template is
normalized by the top-left corner of its bounding box, not by an arbitrary first
cell.

Evidence from visible train 3: the green cells form offsets
`(0,0),(0,1),(1,0),(2,0)`. The colored cells 1, 4, 6, and 7 each become that
same L shape with their original cell as bounding-box origin.

## Largest-component disambiguation

Visible train 1 contains a five-cell connected green template and a separate
green singleton. Only the five-cell object is copied; the singleton is preserved.
Therefore choose the unique largest 4-connected green component rather than all
green cells or the first/smallest green object.

## Implementation

1. Enumerate 4-connected components of color 3.
2. Select the largest component.
3. Normalize its cells by minimum row and minimum column.
4. Snapshot every nonzero, non-green input cell as a marker.
5. Paint the normalized offsets at every marker in that marker's color, while
   preserving the original grid.

The generated examples keep stamps in bounds; the implementation retains a
bounds guard for robustness.
