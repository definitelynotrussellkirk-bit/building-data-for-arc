# Solve work log

## Exposure statement

Before this solve I had not opened the task's Racket rule, generator, notes,
reference solution, private query labels, or earlier solution explanations.  I
used only the visible examples produced by `python3 review.py blind prepare` and
`WORK/solve-blind/challenge.json`.

## Initial observations

Each example contains several nested, disconnected gray rectangular frames, one
purple three-cell marker, and one or more red cells.  The only changed cells are
one complete gray frame, recolored azure; all marker cells and all other frames
are preserved.

Across the three demonstrations:

- one red cell selects the outermost gray frame;
- two red cells select the second frame from the outside;
- three red cells select the third frame from the outside.

The purple marker changes position across examples but does not affect which
frame is recolored, so I treated it as a distractor rather than as an orientation
cue.

## Implementation hypothesis

Count red cells to obtain a one-based frame index.  Find all four-connected gray
components, sort them from outermost to innermost by bounding-box area, and
recolor the selected component azure.  This avoids relying on fixed grid sizes,
frame spacing, or hard-coded coordinates.  Component size is retained as a
stable tie-breaker, although proper nested rectangular frames should already
have distinct bounding-box areas.

## Alternatives considered

I considered selecting a frame by distance from the purple marker or by the red
cells' locations.  Those explanations are unnecessary and inconsistent with the
simple red-count progression visible across all three demonstrations.  I also
considered scanning for exact rectangular borders, but connected components are
simpler and preserve the full observed frame even if dimensions vary.

## Remaining uncertainty

The visible data do not prove behavior for malformed inputs with no red cells,
more red cells than frames, or non-frame gray components.  The implementation
leaves such inputs unchanged rather than guessing.  For the demonstrated task
domain, the red count is within the number of nested frames.
