# Solve work log

I had no earlier exposure to task `4dd02f124024` and did not consult any rule,
generator, reference solution, private label, or prior solve notes.

## Revision 1

Observation: every example has one very rare nonzero color (9, 1, 8, or 6).
Its pixels occur only in the interior of one or more complete monochrome
rectangular frames.  The output changes exactly those marked frames: every
strictly interior cell is erased to background, leaving a clean hollow frame.
Other unmarked objects, even when their interiors are irregular, are unchanged.

Program: locate complete same-color rectangular frames by connected components
and bounding boxes; identify the rare marker by containment inside frames of
other colors (frequency breaks ties); clear the strict interior of each frame
that contains a marker.  As a defensive fallback, erase any remaining marker
pixels.  This predicts that query 0 cleans the color-2 and color-4 frames but
leaves colors 7 and 5 intact, and query 1 cleans only the color-2 frame.

Remaining uncertainty: the examples always use complete outer borders and an
ordinary zero background.  The implementation intentionally follows those
visible invariants rather than guessing behavior for broken borders.
