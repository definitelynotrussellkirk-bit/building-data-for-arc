# Solve work log

## Prior exposure

Before this blind solve I had read only the packet-level handoff documents and the assignment text. I had not opened task `0f7d80015d9d`'s generator, rule, notes, solutions, audit records, or private labels. I also had not opened the assigned repair generator. No earlier rule exposure is known.

## Visible-example observations

All examples contain a solid color-5 rectangle near the bottom, one color-2 marker, and one color-8 marker above it on the same row. In every output:

1. the original 2 is erased;
2. a 2 appears at the 8's old position; and
3. the 8 appears beside a lower corner of the rectangle: immediately left of the lower-left corner when the input 8 is left of the input 2, and immediately right of the lower-right corner when it is right of the 2.

The test inputs separate the markers vertically, so the side decision should use their horizontal order rather than requiring them to share a row. The rectangle's lower side and horizontal extent determine the new 8 location.

## Alternatives considered

I considered a literal clockwise corner rotation and a path-length/offset interpretation. Those do not consistently explain examples 2–4: the markers are not always over the rectangle's exact corners, while the output 8 is always exactly one cell outside a lower corner. The simpler side-selection rule explains all four visible examples and naturally extends to the vertically separated test markers.

## Revision 1

Implemented a direct transformation: infer the background as the modal color, locate the unique 2 and 8, locate the color-5 rectangle bounds, move 2 to the old 8 cell, and put 8 just outside the lower-left or lower-right corner according to whether its input column is left or right of the input 2. The implementation copies the grid and leaves all other cells unchanged.

Remaining uncertainty: the visible data do not show equal marker columns or a non-rectangular color-5 object. Neither occurs in the prepared episode.
