# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
labels, audit evidence, or any earlier solution explanation before this solve.
I used only the prepared visible examples and local Python checks.

## Observation and hypothesis

The first row is a left-to-right color key.  Every remaining nonzero cell has
color 8 and belongs to a 4-connected object.  The number of key colors equals
the number of gray objects.

Across all four demonstrations, ordering the gray objects by decreasing cell
count gives the same order as the key colors:

- example 0: object sizes 5, 4, 2, 1 map to 7, 9, 1, 6;
- example 1: sizes 4, 3, 1 map to 4, 6, 1;
- example 2: sizes 3, 1 map to 5, 6;
- example 3: sizes 4, 3, 1 map to 2, 4, 5.

The output preserves each object's orientation and tight bounding box, recolors
it with the matching key color, bottom-aligns all bounding boxes, and places one
blank column between consecutive objects.  The output height is the greatest
object-bounding-box height; its width is the sum of object-bounding-box widths
plus the separator columns.

## Probe and implementation

Before implementing, I ran all visible training pairs against the provided stub;
all four failed with `NotImplementedError`, confirming the check exercised the
missing behavior.  I then implemented 4-neighbor component extraction, decreasing
area order, tight normalization, recoloring, baseline alignment, and packing.

The demonstrations contain no equal-area objects.  I therefore treat size as the
actual rule and use topmost/leftmost position only as a deterministic fallback for
an unseen tie; the tie behavior remains uncertain rather than inferred from data.

## Remaining uncertainty

The examples consistently reserve color 8 for the objects and put every key color
on row 0.  I assume those are task invariants.  I also assume components are
4-connected, because diagonal contact is never needed to explain a demonstration.
