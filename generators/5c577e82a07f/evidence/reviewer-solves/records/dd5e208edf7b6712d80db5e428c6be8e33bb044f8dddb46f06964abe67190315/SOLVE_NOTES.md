# Visible-only solve work log

The three demonstrations show the same per-color operation. Each nonzero color
appears at the four Cartesian corners determined by two rows and two columns.
The output fills the entire perimeter of that axis-aligned rectangle in the
same color while preserving its interior and all zero background cells.

Important edge case from the visible examples: a rectangle may be only two
columns wide (or two rows high). In that case filling both sides can fill the
whole narrow rectangle; a 2x2 rectangle is already complete and remains
unchanged. Colors are processed independently.

Implementation: group coordinates by color, verify that the observed cells are
exactly the four corners, then paint the top, bottom, left, and right borders.
No reference source, generator source, prior solution, or private label was
consulted during this solve episode. I had earlier rule exposure from reviewing
the assigned generator, so this is an exposed fresh-instance check rather than
a blind solve.
