# Visible-only solve notes

## Observation

Every training output is a one-row monochrome bar. Its color is the sole
nonzero input color and its length equals the total number of cells of that
color: 5 appears four times, 2 appears five times, 8 appears three times, and
2 appears three times.

The examples deliberately vary topology: four disconnected corners, a row, a
partly disconnected pattern, and a column all receive the same treatment.
That rules out preserving shape or using only one connected component.

## Hypothesis

Find the sole nonzero color, count all of its cells anywhere in the grid, and
return one row containing that color exactly that many times.

Predicted masked outputs from the visible queries are a length-2 bar of color 8
and a length-10 bar of color 3. I implemented the general count rule and stop if
the input does not have exactly one nonzero color rather than silently guessing.

## Exposure record

I had seen the generator's rule earlier during the repair assignment. During
this solve I used only the newly prepared visible examples and did not reopen or
consult the generator, Racket source, reference labels, or prior solve notes.
