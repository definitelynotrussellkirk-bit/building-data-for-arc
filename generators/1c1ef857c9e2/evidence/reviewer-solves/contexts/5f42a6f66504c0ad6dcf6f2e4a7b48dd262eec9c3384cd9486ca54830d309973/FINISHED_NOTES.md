# Solve work log

## Constraints followed

I used only `challenge.json` and the visible-check command for this solve. I did
not inspect the generator, Racket rule, reference solutions, private labels, or
earlier solution text while deriving and testing this implementation. I had
already been exposed to the repaired task earlier in the review workflow, so the
final solve declaration records `earlier-exposure=yes` rather than claiming a
blind solve.

## Visible-example hypothesis

Each input has a dominant background color and one minority color that draws
complete horizontal and vertical separator lines. The output is filled with the
background color. Its height is one plus the number of complete separator rows;
its width is one plus the number of complete separator columns. Equivalently,
the output gives the number of rectangular regions induced along each axis.

The visible examples support the rule independently:

- 2 complete separator rows and 4 complete separator columns produce a 3 x 5
  background-colored output.
- 2 rows and 5 columns produce 3 x 6.
- 3 rows and 1 column produce 4 x 2.

The two visible queries therefore appear to require 4 x 3 and 4 x 5 solid grids,
respectively. The program computes these dimensions rather than hard-coding
those predictions.

## Implementation and alternatives

`solution.py` finds the modal color, requires exactly one other color, counts
rows/columns entirely made of that color, and returns the induced region grid.
It also rejects empty, ragged, or extra-color inputs loudly. I considered
counting transitions or connected components, but those were unnecessary and
less directly supported: the examples make the full separator lines observable,
and counting them explains every output dimension exactly.

## Remaining uncertainty

The visible data uses exactly two colors and complete, axis-aligned separators.
The solution intentionally does not generalize to broken lines or multiple
separator colors because those variants are not evidenced by this episode.
