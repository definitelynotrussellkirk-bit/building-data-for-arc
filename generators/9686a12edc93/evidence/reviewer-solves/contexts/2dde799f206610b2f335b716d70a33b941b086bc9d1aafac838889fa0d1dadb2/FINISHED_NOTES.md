# Solve notes

The three visible demonstrations suggest an empty-first output. Each nonzero color appears exactly twice. If its two cells share a row or column and every interior cell on that span is zero, the output fills the inclusive segment in that color.

The key negative example is training example 1: color 4 is vertically aligned, but the color-2 endpoint at row 5, column 5 lies inside its span, and color 4 disappears completely. Therefore aligned pairs are not connected through nonzero blockers, and the output is not initialized as a copy of the input.

Predicted queries:

- Query 0: draw clear vertical color 7, clear horizontal color 8, and clear vertical color 4. Omit vertical color 6 because the color-8 endpoint blocks its interior.
- Query 1: draw horizontal color 2. Omit vertical color 4 because the color-2 endpoint blocks its interior.

This is a fresh implementation from the displayed examples. I had earlier rule exposure during generator repair, so the finish record must say `earlier-exposure yes`; I did not consult the reference or generator after this solve episode was prepared.
