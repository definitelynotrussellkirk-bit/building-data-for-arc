# Final-source visible-only solve notes

This solve was prepared after the final generator change. I had earlier exposure to the task's rule during generator review, so this is explicitly not blind. After this preparation I used only the displayed examples and did not reopen the generator, Racket rule, reference solutions, private labels, archived earlier solve, or earlier solution notes.

## Hypothesis

A full uniform row or column is a separator. Sparse source markers lie on one side; the immediately adjacent line across the separator is an aligned key. For each source marker:

- compare its color with the key cell at the same column (horizontal separator) or row (vertical separator);
- if equal, move it to the source-side edge adjacent to the separator;
- if unequal, move it to the far outer edge of the source side;
- restore the original marker cell to the source background.

Ordinary uniform background rows/columns are not separators, so a candidate separator must have a color different from the source-region mode.

## Visible checks

- Example 0 has a horizontal separator at row 10; the key is row 11. Matches land on row 9 and mismatches on row 0.
- Example 1 has a vertical separator at column 3; the key is column 2. Matches land on column 4 and mismatches on column 7.
- Example 2 has a horizontal separator at row 11; the key is row 12. Matches land on row 10 and mismatches on row 0.

The two queries use vertical and horizontal versions respectively, so the same comparison-and-routing rule applies by rotation.
