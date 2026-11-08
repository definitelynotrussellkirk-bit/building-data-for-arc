# Solve notes

## Constraint followed

I used only `solve/challenge.json` and my own reasoning/code during this solve. I had earlier exposure to the task rule while reviewing the generator, so this is explicitly an **earlier-exposed** rather than blind solve. I did not reopen the generator, Racket authority, reference solution, or private labels after this solve episode was prepared.

## Visible-example inference

- There is one non-`0/1/2/5` color on a non-corner border cell. It is an emitter and also the beam color.
- The beam starts inward, coloring only traversed zero cells.
- A `1` mirror maps `(dr, dc)` to `(-dc, -dr)`.
- A `2` mirror maps `(dr, dc)` to `(dc, dr)`.
- A `5` wall stops the beam before the wall cell; leaving the grid also stops it.
- Mirrors, walls, and the emitter remain unchanged.
- Loop detection must use `(row, column, direction)`, not just the cell, because a valid route can cross a cell in a different direction.

## Implementation revision tested

I implemented that rule directly in `solution.py`. Object lookup reads the immutable input while painting goes to a copy, so a later crossing does not mistake a previously painted beam cell for a new object. This is the first and only visible-example check revision for the final generator hash.
