# Post-repair visible-only solve notes

## Exposure status

I had already worked on this task's generator before this episode, so this is **not blind**. During this solve episode I used only `solve/challenge.json`; I did not reopen the generator, Racket rule, private labels, reference solutions, or earlier solution explanations.

## Visible-example hypothesis

Each row is considered independently.

- When a row has exactly two nonzero cells and both have the same color, fill every cell from the left endpoint through the right endpoint with that color.
- Leave all other rows unchanged: blank rows, rows with two different colors, and rows with three same-color cells.

Evidence in the three demonstrations:

- Matching pairs such as the two 2s, 3s, 7s, 4s, and 5s become solid horizontal spans.
- A two-color row (for example 7 and 8, or 6 and 9) stays unchanged.
- A row containing three 9s or three 6s stays unchanged even though one color repeats.

This distinguishes the exact whole-row predicate from the tempting shortcut “fill any color that occurs twice somewhere in the row.”

## Implementation plan

Copy the grid. For every row, collect `(column, color)` for nonzero cells. Only when the list length is two and the colors match, overwrite the inclusive interval between their columns. Return the copy.
