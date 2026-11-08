# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private labels, audit evidence, or prior solution notes. I used only the visible examples in `challenge.json`.

## Hypothesis

The color `5` forms complete horizontal and vertical lines, but a third color is scattered as noise and sometimes overwrites line cells. A true line is recognizable because every cell along that row or column is non-background. The output removes all scattered noise, restores every full line in color `5`, and colors each horizontal/vertical intersection with the third color.

## Probe and implementation

I compared the three visible pairs. Their outputs contain exactly the Cartesian product of the detected full rows and full columns in the marker color: 3×2, 3×4, and 3×4 intersections. I implemented a color-generic version: most frequent color is background, most frequent remaining color is the line color, and the other color is the marker. Rows/columns containing no background are the hidden lines.

Before implementation I ran a local visible-example test against the provided stub and observed the expected `NotImplementedError`. After implementation the same test is used to compare all three visible outputs exactly.

## Remaining uncertainty

The inference assumes exactly three colors and that random noise never fills an entire non-line row or column. Both assumptions hold in every visible example and query presentation. No reference material was consulted.
