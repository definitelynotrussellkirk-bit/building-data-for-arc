# Solve notes

This is a human work log from the visible examples only. I had earlier exposure to the task rule while repairing the generator, so this is not blind; I did not reopen the generator, Racket source, canonical record, or private labels during this episode.

## Revision 1 hypothesis

The color-5 cell in row 0 marks the output column. Every later nonempty row is a horizontal bar. The output preserves the input and writes one digit at the marker column for each bar row.

With no repeated eligible length, the digit is `(length - 1)^2 mod 10`: visible lengths 2, 3, and 5 give 1, 4, and 6. If exactly one bar length repeats among rows whose bar color is not 5, that repeated length is an anchor: repeated-length rows still use `(length - 1)^2`, while other rows use `(length - repeated_length)^2 mod 10`.

A color-5 bar is excluded when deciding which length repeats, as shown by the third visible example: its length-5 row does not create a duplicate with the ordinary length-5 row. It is still a bar whose marker-column digit is written after the eligible repeated length, if any, has been selected.

I implemented that rule directly, preserving every original cell. The two masked inputs were not inspected beyond their visible grids, and no masked output was consulted.
